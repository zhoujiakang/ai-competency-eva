from typing import Any, Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    sender_type: Literal["student", "ai"]
    content: str = Field(min_length=1)


class Candidate(BaseModel):
    id: int
    type: str
    title: str = ""
    content: str
    options: Any | None = None
    answer: str | None = None
    rubric: str | None = None
    difficulty: int = Field(default=1, ge=1)
    assessment_points: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class DialogueRequest(BaseModel):
    topic: str = Field(min_length=1)
    rubric: str = Field(min_length=1)
    history: list[Message] = Field(min_length=1)
    # 当前主题的消息（用于收尾判断/跳过识别）。
    # history 是整场对话，用来保持上下文连续；topic_history 只含本题，
    # 避免上一个主题的"下一题/不会"影响本题判定。留空时回退到 history。
    topic_history: list[Message] = Field(default_factory=list)
    assessment_points: list[str] = Field(default_factory=list)
    topic_turn_count: int = Field(default=0, ge=0)


class DialogueResponse(BaseModel):
    reply: str
    # 本轮的决策：ask_followup（继续追问当前主题）/ next_question（本题结束，进入下一题）
    action: Literal["ask_followup", "next_question"] = "ask_followup"
    source: str = "deepseek"


class ScoreRequest(BaseModel):
    rubric: str = Field(min_length=1)
    history: list[Message] = Field(min_length=1)
    assessment_points: list[str] = Field(default_factory=list)


class ScoreResponse(BaseModel):
    score: float = Field(ge=0, le=100)
    status: Literal["scored"] = "scored"
    reason: str
    evidence: str
    confidence: float = Field(ge=0, le=1)
