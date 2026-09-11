"""流式通道：把图节点里的发言片段实时送到调用方。

**为什么不用 LangGraph 的 `get_stream_writer()`。**
它依赖 LangGraph 内部的一个 contextvar，而这个变量在 **Python 3.10 下不会传播进节点**
（3.11 及以上才正常）。拿不到时节点第一行就抛
`Called get_config outside of a runnable context`，学生端只会看到一个 error 事件——
服务器上跑的正是 Python 3.10，就是在那里踩到的。

这里自己维护一个 contextvar，行为与 Python / LangGraph 版本无关：

    调用方（AssessmentAgent.stream）
        │  with capture_deltas(write):
        ▼
    图节点（dialogue.agent_turn_node）
        │  emit("AI 说的下一小段")
        ▼
    调用方逐个 yield 出去，浏览器侧真正实时

它是**单向、可缺失**的：没有写入器时 emit 静默丢弃，所以节点可以被单元测试直接调用，
不需要为了拿一个 writer 而先搭一套图。
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar

# 写入器签名：接收一段文本，负责把它推给调用方
DeltaWriter = Callable[[str], None]

_writer: ContextVar[DeltaWriter | None] = ContextVar("agent_delta_writer", default=None)


def emit(text: str) -> None:
    """把一个发言片段交给当前写入器；没有写入器时静默丢弃。"""
    writer = _writer.get()
    if writer is not None and text:
        writer(text)


@contextmanager
def capture_deltas(writer: DeltaWriter) -> Iterator[None]:
    """with 块内，节点里的 emit() 会写到 writer；块结束后恢复原状。"""
    token = _writer.set(writer)
    try:
        yield
    finally:
        _writer.reset(token)
