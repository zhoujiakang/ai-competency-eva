"""收尾的确定性规则：哪些情况下**必须**结束当前主题，不给模型自由裁量。

以前这里是一个「收尾判断节点」，跑在生成发言之后。它判得没错，但那时追问已经流到
浏览器了，于是学生先看到一句追问、紧接着又看到下一题。现在它只做一件事：
**在调用模型之前**判断这一轮是不是必须结束本题。

命中就强制走 next_question 动作：不再让模型做决策，直接要一句收尾语，
模型没有机会再追问，也就不会再出现「追问和换题同时发生」。

两条规则：

    1. 学生明确要求结束（下一题 / 跳过 / 给 0 分……）——确定性词表，不交给模型；
    2. 学生在本主题已经说了 max_topic_turns 轮——防止把人困在同一个话题里。

第 1 条不交给模型，是因为模型只盯着「证据够不够」：学生越是不答，它越觉得该继续问。
但学生有权跳过任何主题。
"""

from __future__ import annotations

from collections.abc import Iterable

from app.agent.actions import NEXT_QUESTION
from app.domain.schemas import Message

# 学生明确要求结束当前主题的说法。只放"指令性"的短语，不放"不会"这类可能出现在
# 正常回答里的词——那种由模型按提示词判断，避免误伤。
SKIP_PHRASES = (
    "下一题", "下个题", "下一个题", "跳过", "跳题", "换一题", "换题",
    "不要这题", "这题过", "别问这题", "0分", "零分", "放弃了",
)
SKIP_MAX_CHARS = 40


def wants_to_skip(history: Iterable[Message]) -> bool:
    """学生最后一条消息是不是在明确要求结束当前主题。

    只看最后一条：学生后面又补充了内容，就说明他还想继续说。
    """
    last_student = next(
        (message for message in reversed(list(history)) if message.sender_type == "student"),
        None,
    )
    if last_student is None:
        return False
    text = last_student.content.strip()
    if not text or len(text) > SKIP_MAX_CHARS:
        return False
    return any(phrase in text for phrase in SKIP_PHRASES)


def forced_action(history: Iterable[Message], turn_count: int, max_turns: int) -> str | None:
    """这一轮是否有规则强制结束本题；有就返回动作名，没有返回 None。"""
    if wants_to_skip(history):
        return NEXT_QUESTION
    if max_turns and turn_count >= max_turns:
        return NEXT_QUESTION
    return None
