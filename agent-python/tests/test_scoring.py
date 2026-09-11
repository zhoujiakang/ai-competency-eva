"""评分环节：一次模型调用，按评分标准打分。"""

import anyio

from app.agent.scoring_tool import LlmScoringTool, score_topic
from app.domain.schemas import Message, ScoreRequest, ScoreResponse
from tests.support import FakeLlmClient


def score_request() -> ScoreRequest:
    return ScoreRequest(
        rubric="必须说明目标、角色、约束和输出格式",
        assessment_points=["结构化表达"],
        history=[Message(sender_type="student", content="我先说结论")],
    )


def test_score_topic_returns_the_parsed_result():
    llm = FakeLlmClient(json_result=ScoreResponse(
        score=88, reason="说明了目标和约束", evidence="第 2 轮", confidence=0.8,
    ))

    result = anyio.run(score_topic, llm, score_request())

    assert result.score == 88
    assert result.status == "scored"
    assert llm.calls[0]["kind"] == "json"


def test_score_prompt_receives_rubric_points_and_history():
    llm = FakeLlmClient(json_result=ScoreResponse(
        score=60, reason="一般", evidence="第 1 轮", confidence=0.5,
    ))

    anyio.run(score_topic, llm, score_request())

    user_prompt = llm.calls[0]["user"]
    assert "必须说明目标、角色、约束和输出格式" in user_prompt
    assert "结构化表达" in user_prompt
    assert "student: 我先说结论" in user_prompt


def test_default_tool_runs_the_same_algorithm():
    """默认评分工具就是 score_topic 的一层包装，两者不会各算各的。"""
    llm = FakeLlmClient(json_result=ScoreResponse(
        score=70, reason="一般", evidence="原话", confidence=0.5,
    ))

    result = anyio.run(LlmScoringTool(llm).score, score_request())

    assert result.score == 70
    assert llm.calls[0]["kind"] == "json"
