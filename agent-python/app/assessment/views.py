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
