"""测评相关的读写。

表边界写死在这里，方便一眼看清 Agent 能碰什么：

    只读   questions / class_questions / assessment_tasks   （题目和考察范围由 Java 维护）
    读写   assessments / assessment_questions / assessment_messages / assessment_answers

发题快照、对话记忆、评分结果全部由本服务落库，Java 不再参与测评过程。
"""

import json
from typing import Any

from app.db.pool import Database


def load_list(value: Any) -> list[str]:
    """标签/考察点列存的是 JSON 数组文本，同时兼容历史的分隔符写法。"""
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except (TypeError, ValueError):
        pass
    text = str(value).replace("，", ",").replace("\n", ",")
    return [part.strip() for part in text.split(",") if part.strip()]


def dump_list(values: Any) -> str | None:
    clean = [str(item).strip() for item in (values or []) if str(item).strip()]
    return json.dumps(clean, ensure_ascii=False) if clean else None


class AssessmentRepository:
    def __init__(self, db: Database):
        self._db = db

    # ------------------------------------------------------------ 测评
    async def get_assessment(self, assessment_id: int) -> dict | None:
        async with self._db.cursor() as cursor:
            await cursor.execute("SELECT * FROM assessments WHERE id = %s", (assessment_id,))
            return await cursor.fetchone()

    async def get_task(self, task_id: int) -> dict | None:
        async with self._db.cursor() as cursor:
            await cursor.execute("SELECT * FROM assessment_tasks WHERE id = %s", (task_id,))
            return await cursor.fetchone()

    async def finish_assessment(self, assessment_id: int, total_score: float | None, status: str) -> None:
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """UPDATE assessments
                   SET status = %s, total_score = %s, completed_at = NOW(3), updated_at = NOW(3)
                   WHERE id = %s""",
                (status, total_score, assessment_id),
            )

    async def save_assessment_level(
        self, assessment_id: int, average_score: float | None, ability_level: str
    ) -> None:
        """综合分与能力等级：班级看板、教师端、学生端都读这两个字段。"""
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """UPDATE assessments
                   SET average_score = %s, ability_level = %s, updated_at = NOW(3)
                   WHERE id = %s""",
                (average_score, ability_level, assessment_id),
            )

    async def save_dimension_scores(
        self, assessment_id: int, class_id: int, student_user_id: int, rows
    ) -> None:
        """维度分：一次测评 × 一个维度一行；重复收尾用 ON DUPLICATE KEY UPDATE 保证幂等。"""
        values = [
            (assessment_id, class_id, student_user_id, row.dimension, row.score, row.question_count)
            for row in rows
        ]
        if not values:
            return
        async with self._db.cursor() as cursor:
            await cursor.executemany(
                """INSERT INTO assessment_dimension_scores
                       (assessment_id, class_id, student_user_id, dimension, score, question_count, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, NOW(3))
                   ON DUPLICATE KEY UPDATE
                       score = VALUES(score),
                       question_count = VALUES(question_count),
                       class_id = VALUES(class_id),
                       student_user_id = VALUES(student_user_id)""",
                values,
            )

    async def save_point_scores(
        self, assessment_id: int, class_id: int, student_user_id: int, rows
    ) -> None:
        """考察点分：一次测评 × 一个考察点一行，技能树的数据源。"""
        values = [
            (
                assessment_id, class_id, student_user_id, row.dimension,
                row.assessment_point, row.score, row.question_count,
            )
            for row in rows
        ]
        if not values:
            return
        async with self._db.cursor() as cursor:
            await cursor.executemany(
                """INSERT INTO assessment_point_scores
                       (assessment_id, class_id, student_user_id, dimension, assessment_point,
                        score, question_count, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(3))
                   ON DUPLICATE KEY UPDATE
                       dimension = VALUES(dimension),
                       score = VALUES(score),
                       question_count = VALUES(question_count),
                       class_id = VALUES(class_id),
                       student_user_id = VALUES(student_user_id)""",
                values,
            )

    async def save_assessment_advice(self, assessment_id: int, advice: str | None) -> None:
        """学习建议：收尾时生成一次并落库，结果页与后续报告直接读，不重复生成。"""
        async with self._db.cursor() as cursor:
            await cursor.execute(
                "UPDATE assessments SET advice = %s, updated_at = NOW(3) WHERE id = %s",
                (advice, assessment_id),
            )

    async def save_class_profile(
        self,
        class_id: int,
        student_user_id: int,
        assessment_id: int,
        average_score: float | None,
        ability_level: str | None,
    ) -> None:
        """个人班级画像：一个「学生 × 班级」一行，永远只保留最新一次测评的分数与等级。"""
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """INSERT INTO student_class_profiles
                       (class_id, student_user_id, assessment_id, average_score, ability_level,
                        completed_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, NOW(3), NOW(3))
                   ON DUPLICATE KEY UPDATE
                       assessment_id = VALUES(assessment_id),
                       average_score = VALUES(average_score),
                       ability_level = VALUES(ability_level),
                       completed_at = VALUES(completed_at),
                       updated_at = NOW(3)""",
                (class_id, student_user_id, assessment_id, average_score, ability_level),
            )

    async def list_dimension_scores(self, assessment_id: int) -> list[dict]:
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """SELECT dimension, score, question_count FROM assessment_dimension_scores
                    WHERE assessment_id = %s ORDER BY dimension""",
                (assessment_id,),
            )
            return await cursor.fetchall()

    async def list_point_scores(self, assessment_id: int) -> list[dict]:
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """SELECT dimension, assessment_point, score, question_count
                     FROM assessment_point_scores
                    WHERE assessment_id = %s ORDER BY dimension, assessment_point""",
                (assessment_id,),
            )
            return await cursor.fetchall()

    # ------------------------------------------------------------ 题库（只读）
    async def list_candidates(self, class_id: int) -> list[dict]:
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """SELECT q.id, q.type, q.title, q.content, q.options, q.answer, q.rubric,
                          q.tags, q.assessment_points, q.difficulty
                     FROM class_questions cq
                     JOIN questions q ON q.id = cq.question_id
                    WHERE cq.class_id = %s AND cq.status = 'active' AND q.status = 'active'
                    ORDER BY q.id""",
                (class_id,),
            )
            rows = await cursor.fetchall()
        for row in rows:
            row["tags"] = load_list(row["tags"])
            row["assessment_points"] = load_list(row["assessment_points"])
        return rows

    # ------------------------------------------------------------ 发题快照
    async def list_questions(self, assessment_id: int) -> list[dict]:
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """SELECT * FROM assessment_questions
                    WHERE assessment_id = %s ORDER BY sequence_no""",
                (assessment_id,),
            )
            return await cursor.fetchall()

    async def current_question(self, assessment_id: int) -> dict | None:
        """最近一道还没答完的题；没有就返回 None（该由引擎出下一道）。"""
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """SELECT * FROM assessment_questions
                    WHERE assessment_id = %s AND status <> 'answered'
                    ORDER BY sequence_no DESC LIMIT 1""",
                (assessment_id,),
            )
            return await cursor.fetchone()

    async def save_question_snapshot(self, assessment_id: int, question: dict, sequence_no: int) -> int:
        """把选中的题目冻结成快照，返回这条快照的 id。"""
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """INSERT INTO assessment_questions
                       (assessment_id, question_id, sequence_no, type, content_snapshot, options_snapshot,
                        answer_snapshot, rubric_snapshot, difficulty_snapshot, tags_snapshot,
                        assessment_points_snapshot, status, finished, sent_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'sent', FALSE, NOW(3))""",
                (
                    assessment_id, question["id"], sequence_no, question.get("type"),
                    question.get("content"), question.get("options"), question.get("answer"),
                    question.get("rubric"), question.get("difficulty", 1),
                    dump_list(question.get("tags")), dump_list(question.get("assessment_points")),
                ),
            )
            return int(cursor.lastrowid)

    async def mark_question_answered(self, record_id: int) -> None:
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """UPDATE assessment_questions
                      SET status = 'answered', finished = TRUE, answered_at = NOW(3)
                    WHERE id = %s""",
                (record_id,),
            )

    # ------------------------------------------------------------ 对话记忆
    async def list_messages(self, assessment_id: int) -> list[dict]:
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """SELECT * FROM assessment_messages
                    WHERE assessment_id = %s ORDER BY created_at, id""",
                (assessment_id,),
            )
            return await cursor.fetchall()

    async def list_question_messages(self, record_id: int) -> list[dict]:
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """SELECT * FROM assessment_messages
                    WHERE assessment_question_id = %s ORDER BY sequence_no""",
                (record_id,),
            )
            return await cursor.fetchall()

    async def append_message(self, assessment_id: int, record_id: int, sender_type: str, content: str) -> dict:
        async with self._db.cursor() as cursor:
            await cursor.execute(
                "SELECT COALESCE(MAX(sequence_no), 0) + 1 AS next_no FROM assessment_messages WHERE assessment_question_id = %s",
                (record_id,),
            )
            sequence_no = (await cursor.fetchone())["next_no"]
            await cursor.execute(
                """INSERT INTO assessment_messages
                       (assessment_id, assessment_question_id, sender_type, content, sequence_no, created_at)
                   VALUES (%s, %s, %s, %s, %s, NOW(3))""",
                (assessment_id, record_id, sender_type, content, sequence_no),
            )
            message_id = int(cursor.lastrowid)
        return {
            "id": message_id,
            "assessmentId": assessment_id,
            "assessmentQuestionId": record_id,
            "senderType": sender_type,
            "content": content,
            "sequenceNo": sequence_no,
        }

    # ------------------------------------------------------------ 评分结果
    async def save_answer(
        self,
        record_id: int,
        content: str,
        score: dict | None,
        failure: str | None = None,
        answer_count: int = 1,
    ) -> None:
        """一道题结束时落一条答案。评分失败只记录失败，绝不伪造成 0 分。

        answer_count 与 submitted_at 都必须显式写入：早期版本的建表语句里
        answer_count 是 `INT NOT NULL` 且没有默认值，在 STRICT_TRANS_TABLES 下
        省略它会直接报 (1364, "Field 'answer_count' doesn't have a default value")。
        不依赖默认值，老库新库都能写。
        """
        scored = score is not None
        async with self._db.cursor() as cursor:
            await cursor.execute(
                """INSERT INTO assessment_answers
                       (assessment_question_id, answer_content, answer_count, result_status, score,
                        scoring_reason, scoring_evidence, confidence, submitted_at, scored_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(3),
                           CASE WHEN %s THEN NOW(3) ELSE NULL END)
                   ON DUPLICATE KEY UPDATE
                       answer_content = VALUES(answer_content),
                       answer_count = VALUES(answer_count),
                       result_status = VALUES(result_status),
                       score = VALUES(score),
                       scoring_reason = VALUES(scoring_reason),
                       scoring_evidence = VALUES(scoring_evidence),
                       confidence = VALUES(confidence),
                       scored_at = VALUES(scored_at)""",
                (
                    record_id,
                    content,
                    max(int(answer_count), 1),
                    "scored" if scored else "scoring_failed",
                    score.get("score") if scored else None,
                    score.get("reason") if scored else failure,
                    score.get("evidence") if scored else None,
                    score.get("confidence") if scored else None,
                    scored,
                ),
            )

    async def list_answers(self, record_ids: list[int]) -> list[dict]:
        if not record_ids:
            return []
        placeholders = ",".join(["%s"] * len(record_ids))
        async with self._db.cursor() as cursor:
            await cursor.execute(
                f"SELECT * FROM assessment_answers WHERE assessment_question_id IN ({placeholders})",
                tuple(record_ids),
            )
            return await cursor.fetchall()
