"""出题引擎：决定"继续问当前题 / 换一道题 / 整场结束"。

这是唯一决定换题时机和选题的地方——Java 和前端都不感知它的存在，
测评流程只调用 ``decide(context)`` 拿一个结论。

换策略只改这个文件：

    class CoverageFirst:
        name = "coverage-first"

        def decide(self, context: EngineContext) -> Decision:
            # context 里有本次测评选定的维度/考察点、已出过的题、当前题是否问完……
            ...

    engine = QuestionEngine(CoverageFirst())

当前默认实现是 :class:`RandomEngine`：当前题目问完就从没用过、且在考察范围内的
题目里随机抽一道；没得抽就收尾。策略还没定，先保持随机。
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal, Protocol, Sequence

from app.domain.schemas import Candidate

# continue 继续问当前题；switch 换一道题；finish 整场结束
Action = Literal["continue", "switch", "finish"]


@dataclass(frozen=True)
class EngineContext:
    """出题引擎做决策时能看到的全部信息。"""

    # 班级题库里可用的题目（含维度与考察点）
    candidates: Sequence[Candidate]
    # 本次测评已经出过的题，状态机维护这份列表，保证同一道题不会出现两次
    used_question_ids: frozenset[int] = frozenset()
    # 本次测评选定的考察范围；为空表示不限制
    dimensions: tuple[str, ...] = ()
    assessment_points: tuple[str, ...] = ()
    # 当前正在问的题，以及这道题是否已经问完
    current_question: Candidate | None = None
    current_question_finished: bool = False
    # 期望题数；0 表示不限制
    question_count: int = 0
    completed_count: int = 0


@dataclass(frozen=True)
class Decision:
    action: Action
    question: Candidate | None = None
    reason: str = ""


class Engine(Protocol):
    """出题算法协议。实现 ``decide`` 就能整体替换策略。"""

    name: str

    def decide(self, context: EngineContext) -> Decision:
        ...


def matches_requirement(candidate: Candidate, dimensions: Sequence[str], points: Sequence[str]) -> bool:
    """题目是否落在本次测评选定的考察范围内。"""
    if dimensions and not set(candidate.tags) & set(dimensions):
        return False
    if points and not set(candidate.assessment_points) & set(points):
        return False
    return True


def eligible_candidates(context: EngineContext) -> list[Candidate]:
    """先按考察范围筛；范围内一道都没有时退回全部题库，避免把测评卡死。"""
    scoped = [
        candidate
        for candidate in context.candidates
        if matches_requirement(candidate, context.dimensions, context.assessment_points)
    ]
    return scoped or list(context.candidates)


class RandomEngine:
    """默认算法：当前题没问完就继续；问完了随机换一道没用过的；没得换就收尾。"""

    name = "random"

    def __init__(self, rng: random.Random | None = None):
        # SystemRandom 不参与全局随机种子，避免被业务代码的 seed 影响
        self._rng = rng or random.SystemRandom()

    def decide(self, context: EngineContext) -> Decision:
        if context.current_question is not None and not context.current_question_finished:
            return Decision("continue", reason="当前题目还没问完")
        if context.question_count and context.completed_count >= context.question_count:
            return Decision("finish", reason=f"已达到题数上限 {context.question_count}")
        available = [
            candidate
            for candidate in eligible_candidates(context)
            if candidate.id not in context.used_question_ids
        ]
        if not available:
            return Decision("finish", reason="题库里已经没有没用过的题了")
        return Decision("switch", self._rng.choice(available), f"从 {len(available)} 道没用过的题里随机选一道")


DEFAULT_ENGINE: Engine = RandomEngine()


class QuestionEngine:
    """流程持有的出题引擎；构造时传入别的策略即可整体替换。"""

    def __init__(self, engine: Engine | None = None):
        self.engine = engine or DEFAULT_ENGINE

    def decide(self, context: EngineContext) -> Decision:
        return self.engine.decide(context)

    @property
    def name(self) -> str:
        return getattr(self.engine, "name", type(self.engine).__name__)
