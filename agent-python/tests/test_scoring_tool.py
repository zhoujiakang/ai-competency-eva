"""评分与聚合口径的单元测试：不联网，只验证算术和可替换性。"""

from app.domain.ability_level import DEFAULT_LEVEL_SCALE, level_of, parse_level_scale
from app.domain.aggregation import Aggregator, QuestionScore
from app.domain.vocabulary import UNCLASSIFIED


def test_level_boundaries_match_the_spec():
    assert level_of(None).level == "L0"
    assert level_of(0).level == "L1"
    assert level_of(59.99).level == "L1"
    assert level_of(60).level == "L2"
    assert level_of(70).level == "L3"
    assert level_of(80).level == "L4"
    assert level_of(90).level == "L5"
    assert level_of(100).level == "L5"
    assert level_of(85).name == "人机协同专家"


def test_aggregate_averages_points_then_dimensions():
    aggregation = Aggregator().aggregate([
        QuestionScore(score=60, dimension="AI基础认知", assessment_points=("AI基本概念理解",)),
        QuestionScore(score=90, dimension="AI基础认知", assessment_points=("AI基本概念理解", "AI能力边界认知")),
        QuestionScore(score=100, dimension="提示词工程", assessment_points=("提示词书写",)),
    ])

    points = {row.assessment_point: row.score for row in aggregation.points}
    assert points == {"AI基本概念理解": 75.0, "AI能力边界认知": 90.0, "提示词书写": 100.0}
    dimensions = {row.dimension: row.score for row in aggregation.dimensions}
    assert dimensions == {"AI基础认知": 82.5, "提示词工程": 100.0}
    # 综合分 = 维度分的平均
    assert aggregation.average_score == 91.25
    assert aggregation.level.level == "L5"
    assert aggregation.total_question_count == 3


def test_aggregate_without_questions_is_empty_l0():
    aggregation = Aggregator().aggregate([])

    assert aggregation.average_score is None
    assert aggregation.level.level == "L0"
    assert aggregation.dimensions == ()
    assert aggregation.points == ()


def test_questions_without_points_fall_back_to_their_own_dimension():
    aggregation = Aggregator().aggregate([
        QuestionScore(score=72, dimension="AI工具使用", assessment_points=()),
    ])

    assert aggregation.points == ()
    assert [(row.dimension, row.score) for row in aggregation.dimensions] == [("AI工具使用", 72.0)]
    assert aggregation.average_score == 72.0


def test_questions_without_dimension_go_to_unclassified():
    aggregation = Aggregator().aggregate([
        QuestionScore(score=50, dimension="", assessment_points=("旧考察点",)),
    ])

    assert aggregation.dimensions[0].dimension == UNCLASSIFIED
    assert aggregation.points[0].dimension == UNCLASSIFIED


def test_level_scale_can_be_overridden_without_touching_callers():
    from app.domain.ability_level import AbilityLevel

    scale = (AbilityLevel("A", "自定档", 50.0), AbilityLevel("B", "低档", 0.0))
    aggregation = Aggregator(level_scale=scale).aggregate([QuestionScore(score=60, dimension="D")])

    assert aggregation.level.level == "A"
    assert aggregation.level.name == "自定档"


def test_level_scale_can_come_from_config_text():
    scale = parse_level_scale("70:A:高档,0:B:低档")

    assert [item.level for item in scale] == ["A", "B"]
    assert level_of(75, scale).name == "高档"
    # 空值或写坏的配置都退回内置档位，不影响测评收尾
    assert parse_level_scale("") == DEFAULT_LEVEL_SCALE
    assert parse_level_scale("这不是配置") == DEFAULT_LEVEL_SCALE


def test_points_go_to_their_own_dimension_on_a_multi_dimension_question():
    """题目可以同时属于多个维度，每个考察点按自己的归属进维度。"""
    aggregation = Aggregator().aggregate([
        QuestionScore(score=70, dimension="提示词工程", assessment_points=("提示词书写", "评估AI结果")),
    ])

    assert {row.assessment_point: row.dimension for row in aggregation.points} == {
        "提示词书写": "提示词工程",
        "评估AI结果": "AI结果评估与优化",
    }
    assert {row.dimension: row.score for row in aggregation.dimensions} == {
        "提示词工程": 70.0,
        "AI结果评估与优化": 70.0,
    }
    assert aggregation.average_score == 70.0


def test_tool_usage_points_stay_in_their_dimension():
    """技能树的叶子是考察点：一个考察点一行，同名的题目合并。"""
    aggregation = Aggregator().aggregate([
        QuestionScore(
            score=60,
            dimension="AI工具使用",
            assessment_points=("工具使用能力",),
        ),
        QuestionScore(
            score=90,
            dimension="AI工具使用",
            assessment_points=("工具使用能力", "工作流整合"),
        ),
    ])

    assert {row.assessment_point: row.score for row in aggregation.points} == {
        "工具使用能力": 75.0,   # (60 + 90) / 2
        "工作流整合": 90.0,
    }
    assert {row.assessment_point: row.question_count for row in aggregation.points} == {
        "工具使用能力": 2,
        "工作流整合": 1,
    }
    # 维度分 = 该维度下考察点分的平均
    assert {row.dimension: row.score for row in aggregation.dimensions} == {"AI工具使用": 82.5}
    assert aggregation.average_score == 82.5
