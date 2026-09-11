"""对话图：一个节点，先决策后发言。追问与换题不可能同时发生。"""

import anyio

from app.agent.actions import ASK_FOLLOWUP, NEXT_QUESTION
from app.agent.graphs import build_dialogue_graph
from tests.support import FakeLlmClient, dialogue_state, settings


def run_graph(llm):
    graph = build_dialogue_graph(llm, settings())

    async def run():
        chunks, final = [], None
        async for mode, data in graph.astream(dialogue_state(), stream_mode=["custom", "values"]):
            if mode == "custom":
                chunks.append(data["delta"])
            else:
                final = data
        return "".join(chunks), final

    return anyio.run(run)


def test_the_graph_asks_a_followup_when_the_decision_is_ask_followup():
    llm = FakeLlmClient(decisions=[ASK_FOLLOWUP], replies=["你提到权重比例，能展开说说吗？"])
    chunks, final = run_graph(llm)

    assert chunks == "你提到权重比例，能展开说说吗？"
    assert final["action"] == ASK_FOLLOWUP
    assert [call["kind"] for call in llm.calls] == ["tool", "stream"]


def test_the_graph_ends_the_topic_when_the_decision_is_next_question():
    llm = FakeLlmClient(decisions=[NEXT_QUESTION], replies=["好，这题我们先过。"])
    chunks, final = run_graph(llm)

    assert chunks == "好，这题我们先过。"
    assert final["action"] == NEXT_QUESTION
