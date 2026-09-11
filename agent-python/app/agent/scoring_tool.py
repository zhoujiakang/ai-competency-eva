"""评分能力：给一道已经答完的题按评分标准打分。

这个文件只放「评分」这一件事，三层从下往上：

    score_topic(llm, request)   评分算法本体：拼提示词 + 调一次模型 + 校验结构化输出
    ScoringTool（协议）          评分能力的统一入口，换算法只实现它
    LlmScoringTool              默认实现，把上面的算法包成协议要求的形状

换算法就是换 ScoringTool 的实现，流程代码（app/assessment/flow.py）一行都不用动：

    class MyScoringTool:
        name = "my-algorithm"

        async def score(self, request: ScoreRequest) -> ScoreResponse:
            ...

    flow = AssessmentFlow(agent, repo, settings, scoring_tool=MyScoringTool())

**不在这里的东西**（它们不是评分算法，只是会被很多地方读到的领域概念）：

    app/domain/ability_level.py   等级划档 L0–L5
    app/domain/aggregation.py     题目分 → 考察点分 → 维度分 → 综合分
    app/domain/vocabulary.py      考察点 → 维度的词表镜像
"""

from __future__ import annotations

from typing import Protocol

from app.agent.prompts import SCORING_SYSTEM, SCORING_USER
from app.agent.transcript import render_history, render_points
from app.domain.schemas import ScoreRequest, ScoreResponse
from app.llm.client import LlmClient


async def score_topic(llm: LlmClient, request: ScoreRequest) -> ScoreResponse:
    """评分算法本体：整个评分环节唯一一次模型调用。

    提示词来自 prompts.py 的 SCORING_*，结构化结果由 ScoreResponse 校验
    （llm.json 内部会抠 JSON、校验失败重试一次）。
    """
    return await llm.json(
        system=SCORING_SYSTEM.substitute(),
        user=SCORING_USER.substitute(
            rubric=request.rubric,
            points=render_points(request.assessment_points),
            history=render_history(request.history),
        ),
        schema=ScoreResponse,
    )


class ScoringTool(Protocol):
    """评分算法协议。实现 ``score`` 就能整体替换默认的模型评分。"""

    name: str

    async def score(self, request: ScoreRequest) -> ScoreResponse:
        ...


class LlmScoringTool:
    """默认实现：让模型按评分标准打分，行为与改造前完全一致。"""

    name = "llm"

    def __init__(self, llm: LlmClient):
        self._llm = llm

    async def score(self, request: ScoreRequest) -> ScoreResponse:
        return await score_topic(self._llm, request)
