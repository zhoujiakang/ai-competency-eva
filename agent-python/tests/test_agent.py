"""对话 Agent 门面：把请求翻译成图状态、把图结果翻译成响应。"""

import anyio
import pytest

from app.agent import AssessmentAgent
from app.agent.actions import ASK_FOLLOWUP, NEXT_QUESTION
from app.core.exceptions import ModelReplyError
from tests.support import FakeLlmClient, dialogue_request, settings


def build_agent(**kwargs):
    llm = FakeLlmClient(**kwargs)
    return AssessmentAgent(settings(), llm=llm), llm


def test_reply_reports_a_followup():
    agent, llm = build_agent(decisions=[ASK_FOLLOWUP], replies=["你先说说当时的约束条件。"])
    response = anyio.run(agent.reply, dialogue_request())

    assert response.reply == "你先说说当时的约束条件。"
    assert response.action == ASK_FOLLOWUP
    assert response.source == "fake"
    assert [call["kind"] for call in llm.calls] == ["tool", "stream"]


def test_reply_reports_next_question_when_the_agent_decides_to_move_on():
    agent, _ = build_agent(decisions=[NEXT_QUESTION], replies=["好，这题我们先过。"])
    response = anyio.run(agent.reply, dialogue_request())

    assert response.reply == "好，这题我们先过。"
    assert response.action == NEXT_QUESTION


def test_stream_emits_deltas_then_done():
    agent, _ = build_agent(decisions=[ASK_FOLLOWUP], replies=["先确认目标，再说明约束。"])

    async def collect():
        return [event async for event in agent.stream(dialogue_request())]

    events = anyio.run(collect)
    assert [kind for kind, _ in events[:-1]] == ["delta"]
    assert events[0][1] == "先确认目标，再说明约束。"
    # done 交出来的是对象，不是 JSON 字符串——序列化是传输层的事
    assert events[-1][0] == "done"
    assert events[-1][1].reply == "先确认目标，再说明约束。"
    assert events[-1][1].action == ASK_FOLLOWUP
    assert events[-1][1].source == "fake"


def test_stream_raises_when_the_decided_action_never_produces_a_reply():
    agent, _ = build_agent(decisions=[ASK_FOLLOWUP], replies=['{"reply": "坏"}'])

    async def collect():
        return [event async for event in agent.stream(dialogue_request())]

    with pytest.raises(ModelReplyError):
        anyio.run(collect)
