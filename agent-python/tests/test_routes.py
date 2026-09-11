"""HTTP 契约：不调用真实模型，验证接口形状、鉴权和 SSE 报文格式。"""

import json

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_agent, get_flow
from app.api.main import app
from app.core.config import get_settings
from tests.support import FakeLlmClient, settings


class FakeAgent:
    """替换真实 Agent，只返回可预测的内容。"""

    def __init__(self, reply="好的，继续说说。", action="ask_followup"):
        self._reply = reply
        self._action = action

    async def reply(self, request):
        from app.domain.schemas import DialogueResponse

        return DialogueResponse(reply=self._reply, action=self._action, source="fake")

    async def stream(self, request):
        for chunk in ["你提到", "权重比例。"]:
            yield "delta", chunk
        from app.domain.schemas import DialogueResponse

        yield "done", DialogueResponse(reply="你提到权重比例。", action=self._action, source="fake")



class FakeScoringTool:
    """假的评分工具，用来说明 /score 走的是流程层那一个工具。"""

    name = "fake"

    def __init__(self, score=77.0):
        self.score_value = score

    async def score(self, request):
        from app.domain.schemas import ScoreResponse

        return ScoreResponse(score=self.score_value, reason="假算法", evidence="假证据", confidence=0.9)


class FakeFlow:
    """只实现 /score 需要的部分：路由从 flow 上取 scoring_tool。"""

    def __init__(self, tool=None):
        self.scoring_tool = tool or FakeScoringTool()


@pytest.fixture
def client():
    app.dependency_overrides[get_agent] = lambda: FakeAgent()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth():
    return {"Authorization": f"Bearer {get_settings().service_token}"}


def request_body():
    return {
        "topic": "提示词工程",
        "rubric": "必须说明目标、角色、约束和输出格式",
        "history": [{"sender_type": "student", "content": "我先说结论"}],
    }


def test_requests_without_a_service_token_are_rejected(client):
    assert client.post("/internal/v1/agent/dialogue", json=request_body()).status_code == 401
    assert client.post("/internal/v1/agent/dialogue/stream", json=request_body()).status_code == 401


def test_health_is_open(client):
    assert client.get("/health").status_code == 200


def test_dialogue_returns_reply_and_action(client, auth):
    response = client.post("/internal/v1/agent/dialogue", json=request_body(), headers=auth)
    assert response.status_code == 200
    assert response.json()["reply"] == "好的，继续说说。"
    assert response.json()["action"] == "ask_followup"


def test_dialogue_stream_uses_delta_and_done_events(client, auth):
    with client.stream("POST", "/internal/v1/agent/dialogue/stream", json=request_body(), headers=auth) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    events = [block for block in body.split("\n\n") if block.strip()]
    assert events[0] == 'event: delta\ndata: "你提到"'
    assert events[1] == 'event: delta\ndata: "权重比例。"'
    assert events[2].startswith("event: done\ndata: ")
    done = json.loads(events[2].split("data: ", 1)[1])
    assert done["reply"] == "你提到权重比例。"


def test_score_uses_the_tool_the_assessment_pipeline_uses(client, auth):
    """评分接口不自己造算法：它用的就是流程层持有的那个评分工具。"""
    app.dependency_overrides[get_flow] = lambda: FakeFlow(FakeScoringTool(score=77.0))

    response = client.post(
        "/internal/v1/agent/score",
        json={
            "rubric": "必须说明目标和约束",
            "history": [{"sender_type": "student", "content": "我先说结论"}],
            "assessment_points": ["提示词书写"],
        },
        headers=auth,
    )

    assert response.status_code == 200
    assert response.json()["score"] == 77.0
    assert response.json()["reason"] == "假算法"
