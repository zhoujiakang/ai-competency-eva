"""对话图的状态定义。

状态就是一张在节点之间传递的字典：每个节点读到需要的东西、返回自己改动的部分。
LangGraph 会把返回值合并进状态，不需要节点自己维护全局变量。

想加新能力（比如 ReAct 里的"思考"或"调用工具"），先在这里补字段。

评分没有状态：它是一次「请求 → 结构化结果」的纯函数（见 scoring_tool.py），
所以这里不再有 ScoreState。
"""

from typing import TypedDict

from app.domain.schemas import Message


class DialogueState(TypedDict, total=False):
    """一次对话回合的状态。"""

    # ---- 输入：由 Java 传入 ----
    topic: str                      # 当前主题（上一道题的题干）
    rubric: str                     # 评分关注点
    assessment_points: list[str]    # 考察点
    history: list[Message]          # 整场测评的对话历史
    topic_history: list[Message]    # 当前主题的消息（确定性收尾规则只看这段）
    topic_turn_count: int           # 学生在这个主题上已经说了几轮

    # ---- 节点产出 ----
    reply: str                      # 生成的测评官发言
    action: str                     # 本轮的决策：ask_followup（追问）/ next_question（结束本题）
    attempts: int                   # 已尝试生成几次
    error: str                      # 生成失败时的原因
