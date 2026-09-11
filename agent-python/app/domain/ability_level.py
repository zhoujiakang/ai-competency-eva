"""能力等级划档（L0–L5）。

放在 domain 而不是 agent 里，因为它是一个纯领域规则：测评收尾算等级、学习建议写等级、
接口展示等级，用的都是这里的同一套档位，谁都可能 import 它。

阈值集中在这里，改档位只动这一处。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class AbilityLevel:
    level: str
    name: str
    min_score: float


# 从高到低排列，level_of() 取第一个满足 score >= min_score 的档位
DEFAULT_LEVEL_SCALE: tuple[AbilityLevel, ...] = (
    AbilityLevel("L5", "创新应用者", 90.0),
    AbilityLevel("L4", "人机协同专家", 80.0),
    AbilityLevel("L3", "应用进阶者", 70.0),
    AbilityLevel("L2", "工具使用者", 60.0),
    AbilityLevel("L1", "基础认知者", 0.0),
)
EMPTY_LEVEL = AbilityLevel("L0", "等待启程", 0.0)


def parse_level_scale(raw: str | None) -> tuple[AbilityLevel, ...]:
    """把配置里的「90:L5:创新应用者,80:L4:…」解析成档位；空值或非法值退回内置档位。"""
    if not raw or not raw.strip():
        return DEFAULT_LEVEL_SCALE
    parsed: list[AbilityLevel] = []
    for chunk in raw.split(","):
        parts = [part.strip() for part in chunk.split(":")]
        if len(parts) != 3:
            return DEFAULT_LEVEL_SCALE
        try:
            parsed.append(AbilityLevel(parts[1], parts[2], float(parts[0])))
        except ValueError:
            return DEFAULT_LEVEL_SCALE
    return tuple(parsed) or DEFAULT_LEVEL_SCALE


def level_of(score: float | None, scale: Sequence[AbilityLevel] = DEFAULT_LEVEL_SCALE) -> AbilityLevel:
    """综合分划档；没有测评记录（score 为 None）时是 L0。"""
    if score is None:
        return EMPTY_LEVEL
    for item in scale:
        if score >= item.min_score:
            return item
    return EMPTY_LEVEL
