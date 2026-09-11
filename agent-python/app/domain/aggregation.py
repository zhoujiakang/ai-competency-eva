"""聚合口径：题目分 → 考察点分 → 维度分 → 综合分 → 能力等级。

纯算术，不调模型。放在 domain 而不是 agent 里，因为它是测评领域的结果口径：
测评收尾算分用它、学习建议读它、接口返回它。

口径：

    考察点分 = 该考察点下所有已评分题目的算术平均
    维度分   = 该维度下所有考察点的算术平均
    综合分   = 六个维度分的算术平均（没考到的维度不参与）

评分失败的题目在进入这里之前就被过滤掉了，所以这里是纯粹的算术。
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Sequence

from app.domain.ability_level import DEFAULT_LEVEL_SCALE, EMPTY_LEVEL, AbilityLevel, level_of
from app.domain.vocabulary import UNCLASSIFIED, dimension_of_point


@dataclass(frozen=True)
class QuestionScore:
    """一道已评分题目参与聚合时需要的全部信息。"""

    score: float
    dimension: str
    assessment_points: tuple[str, ...] = ()


@dataclass(frozen=True)
class DimensionScore:
    dimension: str
    score: float
    question_count: int


@dataclass(frozen=True)
class PointScore:
    dimension: str
    assessment_point: str
    score: float
    question_count: int


@dataclass(frozen=True)
class Aggregation:
    average_score: float | None
    level: AbilityLevel
    dimensions: tuple[DimensionScore, ...] = ()
    points: tuple[PointScore, ...] = ()
    total_question_count: int = 0


class Aggregator:
    """默认聚合实现；换口径就换掉它或传入别的档位。"""

    def __init__(self, level_scale: Sequence[AbilityLevel] | None = None):
        self.level_scale = tuple(level_scale) if level_scale else DEFAULT_LEVEL_SCALE

    def aggregate(self, questions: Sequence[QuestionScore]) -> Aggregation:
        if not questions:
            return Aggregation(average_score=None, level=EMPTY_LEVEL)

        # 考察点：技能树的叶子单位，一个考察点一行（同名合并）。
        # 维度以考察点自己的归属为准——题目可以同时属于多个维度，不能拿题目维度
        # 去套每个考察点；对不上词表的（老数据）才回退到题目维度。
        point_scores: "OrderedDict[str, list[float]]" = OrderedDict()
        point_dimension: dict[str, str] = {}
        for item in questions:
            fallback = item.dimension or UNCLASSIFIED
            for point in item.assessment_points:
                point_scores.setdefault(point, []).append(item.score)
                point_dimension.setdefault(point, dimension_of_point(point) or fallback)

        points = tuple(
            PointScore(
                dimension=point_dimension[point],
                assessment_point=point,
                score=round(sum(scores) / len(scores), 2),
                question_count=len(scores),
            )
            for point, scores in point_scores.items()
        )

        # 维度：该维度下考察点分的平均；没有考察点的题目用题目分直接撑起它的维度
        dimension_points: "OrderedDict[str, list[float]]" = OrderedDict()
        dimension_questions: dict[str, int] = {}
        for item in questions:
            fallback = item.dimension or UNCLASSIFIED
            touched = (
                {dimension_of_point(point) or fallback for point in item.assessment_points}
                if item.assessment_points
                else {fallback}
            )
            for dimension in touched:
                dimension_questions[dimension] = dimension_questions.get(dimension, 0) + 1
            if not item.assessment_points:
                dimension_points.setdefault(fallback, []).append(item.score)

        for point in points:
            dimension_points.setdefault(point.dimension, []).append(point.score)

        dimensions = tuple(
            DimensionScore(
                dimension=dimension,
                score=round(sum(scores) / len(scores), 2),
                question_count=dimension_questions.get(dimension, len(scores)),
            )
            for dimension, scores in dimension_points.items()
        )

        average = (
            round(sum(item.score for item in dimensions) / len(dimensions), 2)
            if dimensions
            else None
        )
        return Aggregation(
            average_score=average,
            level=level_of(average, self.level_scale),
            dimensions=dimensions,
            points=points,
            total_question_count=len(questions),
        )
