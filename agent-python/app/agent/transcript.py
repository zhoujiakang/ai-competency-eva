"""把业务数据翻译成给模型看的文本。

历史对话怎么排版、考察点怎么拼接，都收在这里，
这样能力模块里只剩下"调用模型 + 取结果"的逻辑。
"""

from collections.abc import Iterable, Sequence

from app.domain.schemas import Message

EMPTY_POINTS_TEXT = "未提供"


def render_history(history: Iterable[Message]) -> str:
    """把对话历史渲染成 role: content 的纯文本。"""
    return "\n".join(f"{message.sender_type}: {message.content}" for message in history)


def render_points(points: Sequence[str] | None) -> str:
    """把考察点列表渲染成一行文本。"""
    return "、".join(points) if points else EMPTY_POINTS_TEXT
