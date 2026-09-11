"""对话节点：决策 → 发言两次调用；动作决定用哪套提示词；决策失败不卡住学生。"""

import anyio
from langgraph.graph import END, START, StateGraph

from app.agent.actions import ASK_FOLLOWUP, NEXT_QUESTION
from app.agent.dialogue import FALLBACK_CLOSING, agent_turn_node, looks_like_json
from app.agent.prompts import CLOSING_SYSTEM, DECISION_SYSTEM, DIALOGUE_SYSTEM
from app.agent.state import DialogueState
from app.agent.streaming import capture_deltas
from app.domain.schemas import Message
from tests.support import FakeLlmClient, decision_prompt, dialogue_state, settings


def run_node(llm, state, max_topic_turns=6):
    """跑一次节点，收下流式片段和最终状态。

    片段通过 app.agent.streaming 的 contextvar 出来，所以这里模拟调用方的做法：
    用 capture_deltas 把片段收进列表，再跑节点。
    """
    async def run():
        graph = StateGraph(DialogueState)
        graph.add_node("node", agent_turn_node(llm, settings(max_topic_turns=max_topic_turns)))
        graph.add_edge(START, "node")
        graph.add_edge("node", END)
        chunks = []
        with capture_deltas(chunks.append):
            final = await graph.compile().ainvoke(state)
        return "".join(chunks), final

    return anyio.run(run)


def test_looks_like_json_detects_wrappers():
    assert looks_like_json('{"reply": "你好"}')
    assert looks_like_json("```json\n{}")
    assert not looks_like_json("你提到权重比例，能具体说说吗？")


def test_the_decision_round_is_silent_and_asks_with_the_dialogue_prompt():
    """决策轮只调工具、不说话；学生看到的追问来自第二轮的「追问」提示词。"""
    llm = FakeLlmClient(decisions=[ASK_FOLLOWUP], replies=[["你提到", "权重比例，能展开说说吗？"]])
    chunks, final = run_node(llm, dialogue_state())

    assert chunks == "你提到权重比例，能展开说说吗？"
    assert final["action"] == ASK_FOLLOWUP
    assert [call["kind"] for call in llm.calls] == ["tool", "stream"]
    assert decision_prompt(llm.calls[0])[0] == DECISION_SYSTEM.substitute()
    assert llm.calls[1]["system"] == DIALOGUE_SYSTEM.substitute()
    assert llm.calls[0]["tool_choice"] == "required"


def test_the_closing_round_uses_the_closing_prompt():
    llm = FakeLlmClient(decisions=[NEXT_QUESTION], replies=["好，那这题就先到这儿。"])
    chunks, final = run_node(llm, dialogue_state())

    assert chunks == "好，那这题就先到这儿。"
    assert final["action"] == NEXT_QUESTION
    assert llm.calls[1]["system"] == CLOSING_SYSTEM.substitute()


def test_a_very_short_reply_is_still_sent():
    llm = FakeLlmClient(decisions=[ASK_FOLLOWUP], replies=["好的。"])
    chunks, final = run_node(llm, dialogue_state())

    assert chunks == "好的。"
    assert final["action"] == ASK_FOLLOWUP


def test_json_wrapped_reply_is_dropped_and_retried():
    """模型偶尔会把回复包成 JSON，这种内容绝不能流到浏览器。"""
    llm = FakeLlmClient(decisions=[ASK_FOLLOWUP], replies=['{"reply": "不该出现的内容"}', "这是一句正常的追问。"])
    chunks, final = run_node(llm, dialogue_state())

    assert chunks == "这是一句正常的追问。"
    assert final["reply"] == "这是一句正常的追问。"
    assert final["attempts"] == 2


def test_a_useless_reply_is_reported_as_an_error_when_only_asking():
    llm = FakeLlmClient(decisions=[ASK_FOLLOWUP], replies=['{"reply": "坏"}'])
    chunks, final = run_node(llm, dialogue_state())

    assert chunks == ""
    assert final["reply"] == ""
    assert final["action"] == ASK_FOLLOWUP
    assert "不可用" in final["error"]


def test_a_failed_closing_never_strands_the_student():
    """已经决定要结束本题，收尾话术生成失败也必须给出一句话。"""
    llm = FakeLlmClient(decisions=[NEXT_QUESTION], replies=['{"reply": "坏"}'])
    chunks, final = run_node(llm, dialogue_state())

    assert chunks == FALLBACK_CLOSING
    assert final["reply"] == FALLBACK_CLOSING
    assert final["action"] == NEXT_QUESTION
    assert final["error"] == ""


def test_a_failed_decision_falls_back_to_asking_again():
    """决策失败宁可多问一句，也不草率收尾，更不能把话题悬在那儿。"""
    llm = FakeLlmClient(decisions=[None], replies=["你能再说说当时的约束条件吗？"])
    chunks, final = run_node(llm, dialogue_state())

    assert final["action"] == ASK_FOLLOWUP
    assert chunks == "你能再说说当时的约束条件吗？"


def test_an_explicit_skip_skips_the_decision_round_entirely():
    """学生说要下一题：确定性规则直接收尾，连决策轮都不调。"""
    history = [Message(sender_type="student", content="这题不会，直接下一题")]
    llm = FakeLlmClient(decisions=[ASK_FOLLOWUP], replies=["好，这题我们先过。"])
    chunks, final = run_node(llm, dialogue_state(history=history, topic_history=history))

    assert chunks == "好，这题我们先过。"
    assert final["action"] == NEXT_QUESTION
    assert [call["kind"] for call in llm.calls] == ["stream"]      # 没有决策轮
    assert llm.calls[0]["system"] == CLOSING_SYSTEM.substitute()


def test_the_turn_limit_also_skips_the_decision_round():
    llm = FakeLlmClient(decisions=[ASK_FOLLOWUP], replies=["好，这题我们先过。"])
    chunks, final = run_node(llm, dialogue_state(turn_count=6), max_topic_turns=6)

    assert chunks == "好，这题我们先过。"
    assert final["action"] == NEXT_QUESTION
    assert [call["kind"] for call in llm.calls] == ["stream"]


def test_the_skip_path_still_falls_back_when_closing_fails():
    history = [Message(sender_type="student", content="跳过")]
    llm = FakeLlmClient(replies=['{"reply": "坏"}'])
    chunks, final = run_node(llm, dialogue_state(history=history, topic_history=history))

    assert chunks == FALLBACK_CLOSING
    assert final["action"] == NEXT_QUESTION
