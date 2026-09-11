"""数据库行 → 领域对象（入参方向）。

只做形状转换，不含业务判断；流程层拿到的是已经成型的领域对象，
不用在业务代码里来回 `row["xxx"]`。

    to_message           assessment_messages 行 → Message（喂给模型的对话）
    to_candidate         questions 行 → Candidate（出题引擎的候选）
    to_question_scores   题目快照 + 答案 → QuestionScore（聚合的输入）
    dimension_of         题目快照 → 维度
"""

from __future__ import annotations

from app.db.repository import load_list
from app.domain.aggregation import QuestionScore
from app.domain.schemas import Candidate, Message
from app.domain.vocabulary import UNCLASSIFIED


def dimension_of(question: dict) -> str:
    """快照里的维度取 tags 的第一项（建题时写的就是它）；缺失时归入「未分类」。"""
    tags = load_list(question.get("tags_snapshot"))
    return tags[0] if tags else UNCLASSIFIED


def to_message(row: dict) -> Message:
    return Message(sender_type=row["sender_type"], content=row["content"])


def to_candidate(row: dict) -> Candidate:
    return Candidate(
        id=int(row["id"]),
        type=row.get("type") or "DIALOGUE",
        title=row.get("title") or "",
        content=row.get("content") or "",
        options=row.get("options"),
        answer=row.get("answer"),
        rubric=row.get("rubric"),
        difficulty=int(row.get("difficulty") or 1),
        assessment_points=load_list(row.get("assessment_points")),
        tags=load_list(row.get("tags")),
    )


def to_question_scores(questions: list[dict], answers: list[dict]) -> list[QuestionScore]:
    """把「一条答案 + 它对应的题目快照」翻译成聚合用的输入，评分失败的直接跳过。"""
    snapshots = {int(q["id"]): q for q in questions}
    items: list[QuestionScore] = []
    for answer in answers:
        if answer.get("score") is None:
            continue
        question = snapshots.get(int(answer["assessment_question_id"]))
        if question is None:
            continue
        items.append(
            QuestionScore(
                score=float(answer["score"]),
                dimension=dimension_of(question),
                assessment_points=tuple(load_list(question.get("assessment_points_snapshot"))),
            )
        )
    return items
