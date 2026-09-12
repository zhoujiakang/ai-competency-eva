"""测评流程编排。

Java 只负责建测评数据、把请求转发过来；从这里开始全部由本服务决定：

    1. 按测评 id 取出本次的考察范围（维度 / 考察点）；
    2. 出题引擎决定继续问当前题、换一道、还是收尾；
    3. 生成发言（流式）；"追问还是结束本题"由模型在对话里用工具调用表达；
    4. 模型表示本题结束时才评分、写答案，必要时出下一道题；
    5. 全部结束时算总分、收尾。

对外的 SSE 事件一共六种：

    question  出了新题（出题引擎冻结快照后下发）
    delta     AI 发言的片段，逐字流给前端
    answered  某道题问完了并已评分
    finished  整场结束，前端跳结果页
    done      本回合结束（携带这一轮的 reply）
    error     流中途失败（由路由层在异常时补发）

**这个文件只留编排。** 周边的东西都在邻位文件里，改哪一类就翻哪一个：

    mappers.py   数据库行 → 领域对象（Message / Candidate / 聚合输入）
    views.py     数据库行 → 接口响应字典（接口长什么样）
    rubrics.py   题目快照 → 提示词里的评分关注点
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from app.agent import AssessmentAgent
from app.agent.actions import ASK_FOLLOWUP, NEXT_QUESTION
from app.agent.advice import AdviceWriter, RuleBasedAdviceWriter
from app.agent.scoring_tool import LlmScoringTool, ScoringTool
from app.assessment.mappers import to_candidate, to_message, to_question_scores
from app.assessment.rubrics import dialogue_rubric, scoring_rubric
from app.assessment.views import (
    answer_view,
    assessment_view,
    conversation_messages,
    dimension_view,
    point_view,
    question_view,
    snapshot_view,
)
from app.core.config import Settings
from app.db.repository import AssessmentRepository, load_list
from app.domain.ability_level import parse_level_scale
from app.domain.aggregation import Aggregator
from app.domain.schemas import Candidate, DialogueRequest, Message, ScoreRequest
from app.tools.question_selection import EngineContext, QuestionEngine

logger = logging.getLogger("agent.assessment")


class AssessmentFlow:
    def __init__(
        self,
        agent: AssessmentAgent,
        repo: AssessmentRepository,
        settings: Settings,
        engine: QuestionEngine | None = None,
        scoring_tool: ScoringTool | None = None,
        aggregator: Aggregator | None = None,
        advice_writer: AdviceWriter | None = None,
    ):
        self.agent = agent
        self.repo = repo
        self.settings = settings
        self.engine = engine or QuestionEngine()
        # 三件可替换的能力：评分算法、聚合口径、学习建议。
        # 默认行为与改造前一致，换实现只改构造参数，流程代码不动。
        self.scoring_tool = scoring_tool or LlmScoringTool(agent.llm)
        self.advice_writer = advice_writer or RuleBasedAdviceWriter()
        self.aggregator = aggregator or Aggregator(
            level_scale=parse_level_scale(getattr(settings, "ability_levels", ""))
        )

    # ------------------------------------------------------------ 只读
    async def conversation(self, assessment_id: int, student_user_id: int) -> dict:
        """恢复现场：整场对话 + 当前题目，前端刷新页面时用。"""
        assessment = await self._owned(assessment_id, student_user_id)
        messages = await self.repo.list_messages(assessment_id)
        questions = await self.repo.list_questions(assessment_id)
        # 当前题目 = 最后一条还没答完的题；list_questions 已按 sequence_no 升序，
        # 这样不必再多查一次 current_question。
        pending = [row for row in questions if row["status"] != "answered"]
        current = pending[-1] if pending else None
        return {
            "assessment": assessment_view(assessment),
            # 题干在发题时就写进了消息表，这里连题目一起还原，
            # 前端不用再自己拼「我问过什么」。
            "messages": conversation_messages(messages, questions),
            "question": question_view(current) if current else None,
        }

    async def result(self, assessment_id: int, student_user_id: int) -> dict:
        assessment = await self._owned(assessment_id, student_user_id)
        questions = await self.repo.list_questions(assessment_id)
        answers = await self.repo.list_answers([q["id"] for q in questions])
        # 维度分与考察点分是雷达图 / 技能树的数据源，结果页与工作台读的是同一份记录。
        dimensions = await self.repo.list_dimension_scores(assessment_id)
        points = await self.repo.list_point_scores(assessment_id)
        return {
            "assessment": assessment_view(assessment),
            "questions": [snapshot_view(row) for row in questions],
            "answers": [answer_view(row) for row in answers],
            "dimensions": [dimension_view(row) for row in dimensions],
            "points": [point_view(row) for row in points],
            "advice": assessment.get("advice"),
            "hasScoringFailure": any(a["result_status"] == "scoring_failed" for a in answers),
        }

    # ------------------------------------------------------------ 对话回合
    async def chat(self, assessment_id: int, student_user_id: int, content: str = "") -> AsyncIterator[tuple[str, dict]]:
        """一个回合：可能只是开场出题，也可能带学生的回答。

        content 为空表示"开场或继续"，只会检查当前题目；
        有内容表示学生的回答：agent 边流式回复边给出 action——追问就留在本题，
        调用了 next_question 才关题换题。换题的决定权只在 agent 手里。
        """
        assessment = await self._owned(assessment_id, student_user_id)
        if assessment["status"] != "in_progress":
            yield "error", {"message": "测评已结束"}
            return

        text = (content or "").strip()
        current = await self.repo.current_question(assessment_id)
        reply = ""
        action = ASK_FOLLOWUP

        if current is not None and text:
            await self.repo.append_message(assessment_id, current["id"], "student", text)
            # 本题对话只取一次：发言用它渲染提示词，评分也用它，不再各查一遍。
            # 本回合新写的消息按顺序补进这份内存列表，评分时看到的就是完整历史。
            topic_history = await self.repo.list_question_messages(current["id"])
            async for kind, payload in self.agent.stream(
                    await self._dialogue_request(assessment, current, topic_history)):
                if kind == "delta":
                    yield "delta", {"text": payload}
                    continue
                reply = getattr(payload, "reply", "") or ""
                action = getattr(payload, "action", ASK_FOLLOWUP) or ASK_FOLLOWUP
            if reply:
                saved = await self.repo.append_message(assessment_id, current["id"], "ai", reply)
                topic_history.append(saved or {"sender_type": "ai", "content": reply})
            # 只有 agent 自己调用了 next_question，才结束本题；追问时题目原地不动。
            if action == NEXT_QUESTION:
                yield "answered", await self._close_question(current, topic_history)
                current = None

        if current is None:
            # 开场，或上一道题刚收尾：交给出题引擎决定换题还是收尾
            # 本场已出的题只查一次，出题决策与开新题快照共用。
            questions = await self.repo.list_questions(assessment_id)
            decision = self.engine.decide(await self._context(assessment, questions=questions))
            logger.debug("engine=%s action=%s reason=%s", self.engine.name, decision.action, decision.reason)
            if decision.action == "switch" and decision.question is not None:
                record = await self._open_question(assessment, decision.question, questions)
                yield "question", question_view(record)
            else:
                await self._finish(assessment)
                yield "finished", {"assessmentId": assessment_id}

        yield "done", {"reply": reply}

    # ------------------------------------------------------------ 确认结束
    async def complete(self, assessment_id: int, student_user_id: int) -> dict:
        assessment = await self._owned(assessment_id, student_user_id)
        if assessment["status"] == "in_progress":
            current = await self.repo.current_question(assessment_id)
            if current is not None and await self.repo.list_question_messages(current["id"]):
                await self._close_question(current)
            await self._finish(assessment)
        return await self.result(assessment_id, student_user_id)

    # ------------------------------------------------------------ 内部
    async def _owned(self, assessment_id: int, student_user_id: int) -> dict:
        assessment = await self.repo.get_assessment(assessment_id)
        if assessment is None:
            raise LookupError("测评不存在")
        if int(assessment["student_user_id"]) != int(student_user_id):
            raise PermissionError("无权访问该测评")
        return assessment

    async def _context(self, assessment: dict, current_question: Candidate | None = None,
            current_question_finished: bool = True, questions: list[dict] | None = None) -> EngineContext:
        if questions is None:
            questions = await self.repo.list_questions(assessment["id"])
        candidates = await self.repo.list_candidates(assessment["class_id"])
        task = await self.repo.get_task(assessment["task_id"]) if assessment.get("task_id") else None
        return EngineContext(
            candidates=[to_candidate(row) for row in candidates],
            # 状态机维护的"已经出过的题"列表，保证同一道题不会出现两次
            used_question_ids=frozenset(int(q["question_id"]) for q in questions),
            dimensions=tuple(load_list(assessment.get("dimensions"))),
            assessment_points=tuple(load_list(assessment.get("assessment_points"))),
            current_question=current_question,
            current_question_finished=current_question_finished,
            # 教师任务用任务上的题数；自主练习用学生自己选的题量（0 = 不限）。
            question_count=int(
                (task or {}).get("question_count") or assessment.get("question_count") or 0
            ),
            completed_count=sum(1 for q in questions if q["status"] == "answered"),
        )

    async def _open_question(self, assessment: dict, candidate: Candidate,
            existing_questions: list[dict] | None = None) -> dict:
        """把引擎选中的题冻结成快照，返回这条快照。"""
        questions = (
            existing_questions
            if existing_questions is not None
            else await self.repo.list_questions(assessment["id"])
        )
        await self.repo.save_question_snapshot(
            assessment["id"],
            {
                "id": candidate.id,
                "type": candidate.type,
                "content": candidate.content,
                "options": candidate.options,
                "answer": candidate.answer,
                "rubric": candidate.rubric,
                "difficulty": candidate.difficulty,
                "tags": candidate.tags,
                "assessment_points": candidate.assessment_points,
            },
            len(questions) + 1,
        )
        record = await self.repo.current_question(assessment["id"])
        if record is None:
            raise RuntimeError("发题快照写入失败")
        # 题干同时写进对话记录，作为这道题的第一条消息。
        # 不写的话「继续测评 / 刷新页面」时只能从消息表还原现场，
        # 学生看到的就是一堆回答和追问，却看不到自己答的是哪道题。
        await self.repo.append_message(
            assessment["id"], int(record["id"]), "ai", record["content_snapshot"]
        )
        return record

    async def _close_question(self, question: dict, history: list[dict] | None = None) -> dict:
        """一道题问完了：按快照里的评分标准打分，写答案。

        history 由调用方传入时直接用，避免本回合刚读过一次又重读一遍。
        """
        record_id = int(question["id"])
        if history is None:
            history = await self.repo.list_question_messages(record_id)
        student_messages = [m for m in history if m["sender_type"] == "student"]
        answer_content = student_messages[-1]["content"] if student_messages else f"conversation:{len(history)}"
        score: dict | None = None
        failure: str | None = None
        try:
            result = await self.scoring_tool.score(
                ScoreRequest(
                    rubric=scoring_rubric(question),
                    history=[to_message(m) for m in history],
                    assessment_points=load_list(question.get("assessment_points_snapshot")),
                )
            )
            score = {
                "score": result.score,
                "reason": result.reason,
                "evidence": result.evidence,
                "confidence": result.confidence,
            }
        except Exception as exc:  # 评分失败只记录失败，绝不伪造成 0 分
            failure = str(exc)
            logger.warning("score failed question=%s: %s", record_id, exc)
        # answer_count 记的是学生在这个主题上说了几轮；一题都没说（例如直接跳过）时记 1。
        await self.repo.save_answer(
            record_id, answer_content, score, failure, answer_count=len(student_messages) or 1
        )
        await self.repo.mark_question_answered(record_id)
        return {"questionId": record_id, "score": None if score is None else score["score"], "failed": score is None}

    async def _finish(self, assessment: dict) -> None:
        questions = await self.repo.list_questions(assessment["id"])
        answers = await self.repo.list_answers([q["id"] for q in questions])
        failed = any(a["result_status"] == "scoring_failed" for a in answers)
        scored = [float(a["score"]) for a in answers if a["score"] is not None]
        total = round(sum(scored) / len(scored), 2) if scored else None
        # 聚合口径：题目分 → 考察点分 → 维度分 → 综合分 → 等级。
        # 只统计评分成功的题目；重复收尾由写库的 ON DUPLICATE KEY UPDATE 保证幂等。
        aggregation = self.aggregator.aggregate(to_question_scores(questions, answers))
        # 学习建议与雷达图共用同一份聚合结果，在收尾时一次生成、落库，结果页直接读。
        advice = self.advice_writer.write(aggregation)
        await self.repo.finish_assessment(
            assessment["id"], total, "completed_with_scoring_failure" if failed else "completed"
        )
        await self.repo.save_assessment_level(
            assessment["id"], aggregation.average_score, aggregation.level.level
        )
        await self.repo.save_assessment_advice(assessment["id"], advice)
        await self.repo.save_dimension_scores(
            assessment["id"],
            assessment["class_id"],
            assessment["student_user_id"],
            aggregation.dimensions,
        )
        await self.repo.save_point_scores(
            assessment["id"],
            assessment["class_id"],
            assessment["student_user_id"],
            aggregation.points,
        )
        # 个人班级画像：只保留该班级下最新一次测评的分数与等级，供教师端后续使用。
        await self.repo.save_class_profile(
            assessment["class_id"],
            assessment["student_user_id"],
            assessment["id"],
            aggregation.average_score,
            aggregation.level.level,
        )

    async def _dialogue_request(self, assessment: dict, question: dict,
            topic_history: list[dict] | None = None) -> DialogueRequest:
        history = await self.repo.list_messages(assessment["id"])
        if topic_history is None:
            topic_history = await self.repo.list_question_messages(question["id"])
        return DialogueRequest(
            topic=question["content_snapshot"],
            rubric=dialogue_rubric(question),
            history=[to_message(m) for m in history] or [Message(sender_type="student", content="开始")],
            topic_history=[to_message(m) for m in topic_history],
            assessment_points=load_list(question.get("assessment_points_snapshot")),
            topic_turn_count=sum(1 for m in topic_history if m["sender_type"] == "student"),
        )
