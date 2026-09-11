"""流式通道：emit 把片段交给当前 capture 的写入器，没有写入器时静默。"""

import anyio

from app.agent.streaming import capture_deltas, emit


def test_emit_goes_to_the_active_writer():
    chunks: list[str] = []
    with capture_deltas(chunks.append):
        emit("先确认目标")
        emit("，再说明约束。")

    assert "".join(chunks) == "先确认目标，再说明约束。"


def test_emit_is_silent_without_a_writer():
    """没有写入器时不能报错：节点要能被单测直接调用。"""
    emit("没人接就拿去丢掉")


def test_capture_restores_the_previous_writer():
    outer: list[str] = []
    inner: list[str] = []

    with capture_deltas(outer.append):
        emit("外层")
        with capture_deltas(inner.append):
            emit("内层")
        emit("回到外层")

    assert outer == ["外层", "回到外层"]
    assert inner == ["内层"]


def test_emit_is_visible_inside_a_graph_node():
    """回归：服务器（Python 3.10）上 LangGraph 的 get_stream_writer() 拿不到上下文，
    所以我们用自己的 contextvar——这条用例保证它在图节点里同样可见。"""
    from typing import TypedDict

    from langgraph.graph import END, START, StateGraph

    class State(TypedDict, total=False):
        seen: bool

    def node(state: State) -> dict:
        emit("来自节点")
        return {"seen": True}

    graph = StateGraph(State)
    graph.add_node("n", node)
    graph.add_edge(START, "n")
    graph.add_edge("n", END)
    compiled = graph.compile()

    chunks: list[str] = []

    async def run():
        with capture_deltas(chunks.append):
            return await compiled.ainvoke({})

    final = anyio.run(run)

    assert chunks == ["来自节点"]
    assert final["seen"] is True
