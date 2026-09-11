"""词表映射：考察点 → 维度，以及与 Java 词表的一致性。

最后一条最重要：Python 侧的词表是 Java 枚举的镜像，两份如果漂移，
聚合出来的维度分就会悄悄错位。所以直接解析 Java 源文件做比对。
"""

import re
from pathlib import Path

import pytest

from app.domain import vocabulary as vocab

JAVA_DOMAIN = (
    Path(__file__).resolve().parents[2]
    / "backend-java/src/main/java/com/huiqiyikang/assessment/domain"
)


def test_twenty_points_across_six_dimensions():
    assert len(vocab.POINT_DIMENSIONS) == 20
    assert set(vocab.POINT_DIMENSIONS.values()) <= set(vocab.DIMENSIONS)
    assert len(vocab.DIMENSIONS) == 6


def test_known_points_resolve_to_their_dimension():
    assert vocab.dimension_of_point("AI基本概念理解") == "AI基础认知"
    assert vocab.dimension_of_point("提示词书写") == "提示词工程"
    assert vocab.dimension_of_point("工具使用能力") == "AI工具使用"
    assert vocab.dimension_of_point("问责意识") == "AI伦理与合规"


def test_use_scenarios_are_no_longer_points():
    # 8 个使用场景已经并入考察点介绍，不再是考察点
    for scenario in ("文本写作", "编程开发", "数据分析与商业智能"):
        assert vocab.dimension_of_point(scenario) is None
    assert vocab.dimension_of_point("工具使用能力：编程开发") is None


def test_unknown_points_have_no_dimension():
    assert vocab.dimension_of_point("不存在的考察点") is None
    assert vocab.dimension_of_point("") is None


# --------------------------------------------------------------------------
# 与 Java 词表比对：两边不一致时立刻失败，避免静默漂移
# --------------------------------------------------------------------------


def _dimension_labels(source: str) -> dict[str, str]:
    """AiDimension 的常量名 → 维度中文名。"""
    pairs = re.findall(r"^\s*([A-Z][A-Z0-9_]*)\(\s*\"([^\"]+)\"\s*,", source, re.MULTILINE)
    return dict(pairs)


def _read(name: str) -> str:
    path = JAVA_DOMAIN / name
    if not path.exists():
        pytest.skip(f"找不到 Java 词表 {path}")
    return path.read_text(encoding="utf-8")


def test_point_vocabulary_matches_java_enum():
    dimensions = _dimension_labels(_read("AiDimension.java"))
    entries = re.findall(
        r"([A-Z][A-Z0-9_]*)\(\s*AiDimension\.([A-Z][A-Z0-9_]*)\s*,\s*\"([^\"]+)\"",
        _read("AiAssessmentPoint.java"),
    )
    java_points = {name: dimensions[constant] for _, constant, name in entries}

    assert java_points == vocab.POINT_DIMENSIONS
    assert set(java_points.values()) <= set(vocab.DIMENSIONS)
