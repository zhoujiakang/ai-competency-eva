"""数据库行 → 接口响应字典（出参方向）。

接口返回哪些字段、字段叫什么名字，只在这个文件里决定。流程层只负责"什么时候发"，
不负责"长什么样"，所以改字段名不用翻编排逻辑。

命名约定：函数名去掉下划线直接对应事件/接口里的含义，例如
`question_view` 就是 SSE 里 `question` 事件的载荷。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.db.repository import load_list


def number(value: Any) -> float | None:
    """MySQL 的 DECIMAL 会以 Decimal 返回，统一转成 float 再出接口。"""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def question_view(row: dict) -> dict:
    """给前端的当前题目：只有题面和参考方向，没有"主题""第几题"这些概念。"""
    return {
        "id": int(row["id"]),
        "content": row["content_snapshot"],
        "options": row["options_snapshot"],
    }


def message_view(row: dict) -> dict:
    return {
        "id": int(row["id"]),
        "senderType": row["sender_type"],
        "content": row["content"],
        "assessmentQuestionId": int(row["assessment_question_id"]),
        "sequenceNo": row["sequence_no"],
        "createdAt": iso(row.get("created_at")),
    }


def prompt_message(question: dict) -> dict:
    """合成一条题干消息：老数据没有把它写进消息表，这里按快照补回来。

    合成消息没有数据库 id，所以 id 借用题目记录 id；前端本来就用题目记录 id
    当题目气泡的 key，不受影响。
    """
    question_id = int(question["id"])
    return {
        "id": f"q-{question_id}",
        "senderType": "ai",
        "content": question.get("content_snapshot") or "",
        "assessmentQuestionId": question_id,
        "sequenceNo": 0,
        "createdAt": iso(question.get("sent_at")),
        "questionPrompt": True,
        "questionAnswered": question.get("status") == "answered",
        "synthetic": True,
    }


def conversation_messages(message_rows: list[dict], question_rows: list[dict]) -> list[dict]:
    """恢复现场的对话列表：把每道题的题干放回对话，并标出题目状态。

    新数据在发题时就把题干写进了 assessment_messages（该题第一条消息就是它），
    这里只负责标记成 questionPrompt；老数据没有这条消息，用品快照合成一条，
    否则「刷新页面 / 继续测评」时学生只看到一堆回答和追问，看不到自己在答什么。
    每道题只标第一条，之后的追问与回答都是普通消息。
    """
    answered = {int(row["id"]): row["status"] == "answered" for row in question_rows}
    grouped: dict[int, list[dict]] = {}
    for row in message_rows:
        grouped.setdefault(int(row["assessment_question_id"]), []).append(row)

    messages: list[dict] = []
    known: set[int] = set()
    for question in question_rows:
        question_id = int(question["id"])
        known.add(question_id)
        rows = grouped.get(question_id, [])
        if not rows or rows[0]["sender_type"] != "ai":
            messages.append(prompt_message(question))
        for index, row in enumerate(rows):
            view = message_view(row)
            if index == 0:
                view["questionPrompt"] = row["sender_type"] == "ai"
                view["questionAnswered"] = answered.get(question_id, False)
            messages.append(view)

    # 兜底：题目快照已经不在了、消息还留着的数据。正常流程不会出现，
    # 但真遇到也不能把消息吞掉，否则用户会觉得对话少了内容。
    for question_id, rows in grouped.items():
        if question_id in known:
            continue
        for index, row in enumerate(rows):
            view = message_view(row)
            if index == 0:
                view["questionPrompt"] = False
                view["questionAnswered"] = False
            messages.append(view)
    return messages


def snapshot_view(row: dict) -> dict:
    return {
        "id": int(row["id"]),
        "sequenceNo": row["sequence_no"],
        "type": row["type"],
        "contentSnapshot": row["content_snapshot"],
        "optionsSnapshot": row["options_snapshot"],
        "rubricSnapshot": row["rubric_snapshot"],
        "difficultySnapshot": row["difficulty_snapshot"],
        "tagsSnapshot": load_list(row.get("tags_snapshot")),
        "assessmentPointsSnapshot": load_list(row.get("assessment_points_snapshot")),
        "status": row["status"],
        "finished": bool(row["finished"]),
    }


def answer_view(row: dict) -> dict:
    return {
        "assessmentQuestionId": int(row["assessment_question_id"]),
        "answerContent": row["answer_content"],
        "resultStatus": row["result_status"],
        "score": number(row.get("score")),
        "scoringReason": row.get("scoring_reason"),
        "scoringEvidence": row.get("scoring_evidence"),
        "confidence": number(row.get("confidence")),
    }


def assessment_view(row: dict) -> dict:
    return {
        "id": int(row["id"]),
        "taskId": row.get("task_id"),
        "classId": row.get("class_id"),
        "studentUserId": row.get("student_user_id"),
        "dimensions": load_list(row.get("dimensions")),
        "assessmentPoints": load_list(row.get("assessment_points")),
        "questionCount": int(row.get("question_count") or 0),
        "status": row.get("status"),
        "totalScore": number(row.get("total_score")),
        "averageScore": number(row.get("average_score")),
        "abilityLevel": row.get("ability_level"),
        "advice": row.get("advice"),
        "startedAt": iso(row.get("started_at")),
        "completedAt": iso(row.get("completed_at")),
    }


def dimension_view(row: dict) -> dict:
    return {
        "dimension": row.get("dimension"),
        "score": number(row.get("score")),
        "questionCount": int(row.get("question_count") or 0),
    }


def point_view(row: dict) -> dict:
    return {
        "dimension": row.get("dimension"),
        "assessmentPoint": row.get("assessment_point"),
        "score": number(row.get("score")),
        "questionCount": int(row.get("question_count") or 0),
    }
