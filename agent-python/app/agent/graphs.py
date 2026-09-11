"""对话图：用 LangGraph 把节点连起来。

对话图（每收到一条学生消息跑一次）只有一个节点：

    START ──► agent_turn ──► END

「思考 → 调工具 → 再思考 → 说话」这个 ReAct 循环收在 `agent_turn` 内部
（见 app/agent/dialogue.py），因为它的每一步都要和同一个流式输出通道打交道：
工具调用必须静默、最终发言必须逐字流出去。放在一个节点里，这两条不变量是局部可读的。

所以这里刻意不再有 generate_reply / review_reply / decide_finished 三个节点——
那套结构的问题是"生成"和"收尾判断"各自独立，导致模型刚追问完、系统又发了下一题。
现在决策只有一个来源：模型在 agent_turn 里报告的动作（ask_followup / next_question）。

**这里只有对话图。** 评分不再包一张单节点图：评分压根没有节点间的状态流转，
套一层图只是多一次转手，现在由 `app/agent/scoring_tool.py` 的 `score_topic()`
直接完成那次模型调用。
"""

from langgraph.graph import END, START, StateGraph

from app.agent.dialogue import agent_turn_node
from app.agent.state import DialogueState
from app.core.config import Settings
from app.llm.client import LlmClient


def build_dialogue_graph(llm: LlmClient, settings: Settings):
    graph = StateGraph(DialogueState)

    graph.add_node("agent_turn", agent_turn_node(llm, settings))

    graph.add_edge(START, "agent_turn")
    graph.add_edge("agent_turn", END)
    return graph.compile()
