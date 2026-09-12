"""测评流程：一个回合会吐出哪些 SSE 事件。

用内存假仓库替换 MySQL，验证的是流程本身——什么时候发题、什么时候评分关题、
什么时候收尾，以及"同一道题不重复出现"。
"""

import anyio

from app.assessment import AssessmentFlow
from app.agent import AssessmentAgent
from app.agent.actions import ASK_FOLLOWUP, NEXT_QUESTION
from app.domain.schemas import DialogueResponse, ScoreResponse
from tests.support import FakeLlmClient, settings


class FakeAgent:
    def __init__(self, reply="说得挺完整。", action=NEXT_QUESTION, score=88.0):
        self.reply = reply
        self.action = action
        self.score_value = score
        self.scored = []

    async def stream(self, request):
        for chunk in ["说得", "挺完整。"]:
            yield "delta", chunk
        yield "done", DialogueResponse(reply=self.reply, action=self.action, source="fake")

    async def score(self, request):
        self.scored.append(request)
        return ScoreResponse(score=self.score_value, reason="覆盖了主要维度", evidence="原话", confidence=0.8)


class FakeRepo:
    def __init__(self, questions, assessment=None):
        self._questions = questions
        self.assessment = {
            "id": 1,
            "task_id": None,
            "class_id": 1,
            "student_user_id": 7,
            "dimensions": None,
            "assessment_points": None,
            "status": "in_progress",
            "total_score": None,
            "started_at": None,
            "completed_at": None,
        }
        if assessment:
            self.assessment.update(assessment)
        self.snapshots = []
        self.messages = []
        self.answers = []
        self.dimension_scores = []
        self.point_scores = []
        self.level = None
        self.advice = None
        self.profile = None

    async def get_assessment(self, assessment_id):
        return self.assessment if assessment_id == 1 else None

    async def get_task(self, task_id):
        return {"question_count": 2}

    async def list_candidates(self, class_id):
        return self._questions

    async def list_questions(self, assessment_id):
        return self.snapshots

    async def current_question(self, assessment_id):
        sent = [row for row in self.snapshots if row["status"] != "answered"]
        return sent[-1] if sent else None

    async def save_question_snapshot(self, assessment_id, question, sequence_no):
        self.snapshots.append({
            "id": len(self.snapshots) + 1,
            "assessment_id": assessment_id,
            "question_id": question["id"],
            "sequence_no": sequence_no,
            "type": question["type"],
            "content_snapshot": question["content"],
            "options_snapshot": question.get("options"),
            "rubric_snapshot": question.get("rubric"),
            "answer_snapshot": question.get("answer"),
            "difficulty_snapshot": question.get("difficulty"),
            "tags_snapshot": question.get("tags"),
            "assessment_points_snapshot": question.get("assessment_points"),
            "status": "sent",
            "finished": False,
        })
        return self.snapshots[-1]["id"]

    async def mark_question_answered(self, record_id):
        for row in self.snapshots:
            if row["id"] == record_id:
                row["status"] = "answered"
                row["finished"] = True

    async def list_messages(self, assessment_id):
        return self.messages

    async def list_question_messages(self, record_id):
        return [m for m in self.messages if m["assessment_question_id"] == record_id]

    async def append_message(self, assessment_id, record_id, sender_type, content):
        sequence_no = len([m for m in self.messages if m["assessment_question_id"] == record_id]) + 1
        self.messages.append({
            "id": len(self.messages) + 1,
            "assessment_id": assessment_id,
            "assessment_question_id": record_id,
            "sender_type": sender_type,
            "content": content,
            "sequence_no": sequence_no,
        })

    async def save_answer(self, record_id, content, score, failure=None, answer_count=1):
        self.answers = [a for a in self.answers if a["assessment_question_id"] != record_id]
        self.answers.append({
            "assessment_question_id": record_id,
            "answer_content": content,
            "answer_count": answer_count,
            "result_status": "scored" if score else "scoring_failed",
            "score": None if score is None else score["score"],
            "scoring_reason": failure if score is None else score["reason"],
            "scoring_evidence": None if score is None else score["evidence"],
            "confidence": None if score is None else score["confidence"],
        })

    async def list_answers(self, record_ids):
        return self.answers

    async def finish_assessment(self, assessment_id, total_score, status):
        self.assessment["status"] = status
        self.assessment["total_score"] = total_score

    async def save_assessment_level(self, assessment_id, average_score, ability_level):
        self.level = {"average_score": average_score, "ability_level": ability_level}

    async def save_dimension_scores(self, assessment_id, class_id, student_user_id, rows):
        self.dimension_scores = list(rows)

    async def save_point_scores(self, assessment_id, class_id, student_user_id, rows):
        self.point_scores = list(rows)

    async def save_assessment_advice(self, assessment_id, advice):
        self.advice = advice
        # 真实仓库是 UPDATE assessments，这里同步到内存记录，result() 才能读到。
        self.assessment["advice"] = advice

    async def save_class_profile(self, class_id, student_user_id, assessment_id, average_score, ability_level):
        self.profile = {
            "class_id": class_id,
            "student_user_id": student_user_id,
            "assessment_id": assessment_id,
            "average_score": average_score,
            "ability_level": ability_level,
        }

    async def list_dimension_scores(self, assessment_id):
        return [
            {"dimension": row.dimension, "score": row.score, "question_count": row.question_count}
            for row in self.dimension_scores
        ]

    async def list_point_scores(self, assessment_id):
        return [
            {
                "dimension": row.dimension,
                "assessment_point": row.assessment_point,
                "score": row.score,
                "question_count": row.question_count,
            }
            for row in self.point_scores
        ]


def question(question_id, tags=None, points=None):
    return {
        "id": question_id,
        "type": "DIALOGUE",
        "title": f"题目 {question_id}",
        "content": f"题目 {question_id} 的题干",
        "options": None,
        "answer": None,
        "rubric": "评分标准",
        "tags": tags or [],
        "assessment_points": points or [],
        "difficulty": 2,
    }


def run(flow, *args):
    async def collect():
        return [event async for event in flow.chat(*args)]

    return anyio.run(collect)


def build_flow(agent, repo, **kwargs):
    """假 Agent 同时充当评分工具：它的 score() 是脚本化的。

    生产环境里 flow 默认用 LlmScoringTool(agent.llm)，测试里用假 Agent 的
    score() 顶替，这样流程测试完全不碰模型（真实 Agent 那一版见
    test_a_skip_always_closes_the_topic_and_moves_on）。
    """
    kwargs.setdefault("scoring_tool", agent)
    return AssessmentFlow(agent, repo, settings(), **kwargs)


def test_opening_a_run_sends_a_question_and_nothing_else():
    repo = FakeRepo([question(11), question(12)])
    flow = build_flow(FakeAgent(), repo)

    events = run(flow, 1, 7, "")

    assert [kind for kind, _ in events] == ["question", "done"]
    assert events[0][1]["content"] == "题目 11 的题干" or events[0][1]["content"].startswith("题目 1")
    assert repo.snapshots[0]["status"] == "sent"


def test_a_question_the_agent_ended_is_scored_and_swapped_for_the_next_one():
    repo = FakeRepo([question(11), question(12), question(13)])
    agent = FakeAgent(action=NEXT_QUESTION)
    flow = build_flow(agent, repo)
    run(flow, 1, 7, "")  # 开场：出第一道题

    events = run(flow, 1, 7, "我的回答")

    kinds = [kind for kind, _ in events]
    assert kinds == ["delta", "delta", "answered", "question", "done"]
    assert repo.snapshots[0]["status"] == "answered"
    assert repo.answers[0]["result_status"] == "scored"
    # 老库的 answer_count 没有默认值，必须由写库方显式提供
    assert repo.answers[0]["answer_count"] == 1
    assert len(repo.snapshots) == 2
    assert repo.snapshots[0]["question_id"] != repo.snapshots[1]["question_id"]


def test_answer_count_counts_the_student_turns_in_one_topic():
    class TwoTurnAgent(FakeAgent):
        """第一轮还没问完，第二轮才收尾。"""

        def __init__(self):
            super().__init__(action=ASK_FOLLOWUP)
            self.calls = 0

        async def stream(self, request):
            self.calls += 1
            self.action = NEXT_QUESTION if self.calls >= 2 else ASK_FOLLOWUP
            async for item in super().stream(request):
                yield item

    repo = FakeRepo([question(11), question(12)])
    flow = build_flow(TwoTurnAgent(), repo)
    run(flow, 1, 7, "")             # 开场：出第一道题
    run(flow, 1, 7, "第一段回答")    # 本题还没问完
    events = run(flow, 1, 7, "第二段回答")  # 问完并评分

    assert "answered" in [kind for kind, _ in events]
    assert repo.answers[0]["answer_count"] == 2
    assert repo.answers[0]["answer_content"] == "第二段回答"

def test_the_run_finishes_when_no_unused_question_is_left():
    repo = FakeRepo([question(11)])
    flow = build_flow(FakeAgent(action=NEXT_QUESTION), repo)
    run(flow, 1, 7, "")

    events = run(flow, 1, 7, "我的回答")

    assert [kind for kind, _ in events] == ["delta", "delta", "answered", "finished", "done"]
    assert repo.assessment["status"] == "completed"
    assert repo.assessment["total_score"] == 88.0


def test_a_followup_keeps_the_conversation_on_the_same_question():
    """回归：agent 只是追问时，绝不能顺手把下一题也发出来。

    这正是原来的 bug——模型追问的同时，流程层按自己的判断换了题。
    """
    repo = FakeRepo([question(11), question(12)])
    flow = build_flow(FakeAgent(action=ASK_FOLLOWUP), repo)
    run(flow, 1, 7, "")

    events = run(flow, 1, 7, "还没说完")

    assert [kind for kind, _ in events] == ["delta", "delta", "done"]
    assert len(repo.snapshots) == 1
    assert repo.snapshots[0]["status"] == "sent"
    assert repo.answers == []


def test_scoring_failure_is_recorded_as_failure_not_zero():
    class FailingAgent(FakeAgent):
        async def score(self, request):
            raise RuntimeError("model down")

    repo = FakeRepo([question(11), question(12)])
    flow = build_flow(FailingAgent(), repo)
    run(flow, 1, 7, "")

    run(flow, 1, 7, "我的回答")

    assert repo.answers[0]["result_status"] == "scoring_failed"
    assert repo.answers[0]["score"] is None


def test_scoring_sees_the_ai_reply_from_the_same_turn():
    """评分历史必须含本回合刚生成的 AI 回复。

    流程把本题对话读一次后在本回合内复用（省掉重复查询），新写的 AI 回复要补进
    这份内存历史；漏补的话评分看到的对话就少了最后一轮，理由会变得没有依据。
    """
    agent = FakeAgent(reply="说得挺完整。", action=NEXT_QUESTION)
    repo = FakeRepo([question(11), question(12)])
    flow = build_flow(agent, repo)
    run(flow, 1, 7, "")                     # 开场：出第一道题

    run(flow, 1, 7, "我的回答")

    scored_history = [(m.sender_type, m.content) for m in agent.scored[0].history]
    # 第一句是题干（发哪道题由出题引擎随机决定），随后才是本轮的问答；
    # 题干现在也落进了对话记录，评分看到的上下文因此是完整的。
    assert scored_history[0] == ("ai", repo.snapshots[0]["content_snapshot"])
    assert scored_history[1:] == [("student", "我的回答"), ("ai", "说得挺完整。")]


def test_the_question_prompt_is_written_into_the_transcript():
    """发题时题干要落进对话记录。

    否则「继续测评 / 刷新页面」只能从消息表还原现场，学生看到一堆回答和追问，
    却看不到自己答的是哪道题。
    """
    repo = FakeRepo([question(11), question(12)])
    flow = build_flow(FakeAgent(action=NEXT_QUESTION), repo)

    run(flow, 1, 7, "")   # 开场：出第一道题

    prompt = repo.messages[0]
    assert prompt["sender_type"] == "ai"
    assert prompt["content"] == repo.snapshots[0]["content_snapshot"]
    assert prompt["assessment_question_id"] == repo.snapshots[0]["id"]


def test_conversation_marks_the_prompt_and_the_answered_state():
    """恢复现场：题干标成 questionPrompt，答完的题目标成已答完。"""
    repo = FakeRepo([question(11), question(12)])
    flow = build_flow(FakeAgent(action=NEXT_QUESTION), repo)
    run(flow, 1, 7, "")             # 出第一道题
    run(flow, 1, 7, "我的回答")      # 答完并换到第二道题

    async def collect():
        return await flow.conversation(1, 7)

    data = anyio.run(collect)
    prompts = [m for m in data["messages"] if m.get("questionPrompt")]
    assert len(prompts) == 2                    # 两道题的题干都在记录里
    assert prompts[0]["questionAnswered"] is True    # 第一题已答完
    assert prompts[1]["questionAnswered"] is False   # 第二题正在问
    assert data["question"]["content"] == prompts[1]["content"]


def test_legacy_questions_without_a_prompt_message_still_show_the_question():
    """历史数据没有题干消息（题干入消息表是后加的），恢复现场时要按快照补一条。

    不补的话，老测评刷新后只剩学生回答和 AI 追问，看不到自己在答什么。
    """
    repo = FakeRepo([question(11), question(12)])
    flow = build_flow(FakeAgent(action=NEXT_QUESTION), repo)
    run(flow, 1, 7, "")             # 出第一道题（会写题干消息）
    run(flow, 1, 7, "我的回答")      # 答完并换到第二道题
    first_prompt = repo.snapshots[0]["content_snapshot"]
    repo.messages = [m for m in repo.messages if m["content"] != first_prompt]  # 退回改造前

    async def collect():
        return await flow.conversation(1, 7)

    data = anyio.run(collect)
    prompts = [m for m in data["messages"] if m.get("questionPrompt")]
    assert len(prompts) == 2
    assert prompts[0]["content"] == first_prompt
    assert prompts[0]["synthetic"] is True            # 第一题：快照补出来的
    assert prompts[0]["questionAnswered"] is True
    assert prompts[1].get("synthetic") is None        # 第二题：消息表里本来就有


def test_a_skip_always_closes_the_topic_and_moves_on():
    """回归：学生说"不会 / 下一题"，这一回合必须真的关题并出下一题。

    曾经出现过模型嘴上收尾、决策却被丢掉的情况，学生就卡在一条没有下文的话题里：
    既不追问，也不出下一题，也不结束测评。这条用例用真实 Agent 走完整回合。
    """
    llm = FakeLlmClient(
        decisions=[NEXT_QUESTION],
        replies=["好，那这题我们就先到这里。"],
        json_result=ScoreResponse(score=0, reason="学生未作答", evidence="这题不会，下一题", confidence=0.9),
    )
    repo = FakeRepo([question(11), question(12)])
    flow = AssessmentFlow(AssessmentAgent(settings(), llm=llm), repo, settings())
    run(flow, 1, 7, "")                          # 开场：出第一道题

    events = run(flow, 1, 7, "这题不会，下一题")

    kinds = [kind for kind, _ in events]
    assert kinds == ["delta", "answered", "question", "done"]
    assert repo.snapshots[0]["status"] == "answered"
    assert len(repo.snapshots) == 2              # 新题真的开出来了
    assert repo.answers[0]["result_status"] == "scored"
    # 确定性规则直接收尾，连决策轮都不用调
    assert [call["kind"] for call in llm.calls] == ["stream", "json"]


class SequencedAgent(FakeAgent):
    """按脚本依次给出不同的分数，用来验证聚合口径。"""

    def __init__(self, scores):
        super().__init__(action=NEXT_QUESTION)
        self._scores = list(scores)

    async def score(self, request):
        self.scored.append(request)
        return ScoreResponse(score=self._scores.pop(0), reason="脚本分数", evidence="原话", confidence=0.5)


class FakeScoringTool:
    """可替换的评分工具：证明流程不依赖具体算法。"""

    name = "fake-scoring"

    def __init__(self, score=42.0):
        self.score_value = score
        self.requests = []

    async def score(self, request):
        self.requests.append(request)
        return ScoreResponse(score=self.score_value, reason="假算法", evidence="假证据", confidence=1.0)


def test_scoring_can_be_replaced_by_a_custom_tool():
    tool = FakeScoringTool(score=42.0)
    agent = FakeAgent(action=NEXT_QUESTION)
    repo = FakeRepo([question(11)])
    flow = build_flow(agent, repo, scoring_tool=tool)
    run(flow, 1, 7, "")

    run(flow, 1, 7, "我的回答")

    assert len(tool.requests) == 1
    assert agent.scored == []                      # 默认评分图没有被调用
    assert repo.answers[0]["score"] == 42.0
    assert repo.level["ability_level"] == "L1"     # 42 分 → L1


def test_each_tool_gets_one_score_request_per_closed_question():
    tool = FakeScoringTool(score=80.0)
    repo = FakeRepo([question(11), question(12)])
    flow = build_flow(FakeAgent(action=NEXT_QUESTION), repo, scoring_tool=tool)
    run(flow, 1, 7, "")
    run(flow, 1, 7, "回答一")
    run(flow, 1, 7, "回答二")

    assert len(tool.requests) == 2
    assert all(request.assessment_points == [] for request in tool.requests)


def test_finish_writes_dimension_and_point_scores_and_level():
    repo = FakeRepo([
        question(11, tags=["AI基础认知"], points=["AI基本概念理解"]),
        question(12, tags=["AI伦理与合规"], points=["隐私保护意识"]),
    ])
    flow = build_flow(SequencedAgent([60.0, 90.0]), repo)
    run(flow, 1, 7, "")
    run(flow, 1, 7, "回答一")
    run(flow, 1, 7, "回答二")

    # 综合分 = 两个维度分的平均 = (60 + 90) / 2
    assert repo.level == {"average_score": 75.0, "ability_level": "L3"}
    assert {row.score for row in repo.dimension_scores} == {60.0, 90.0}
    assert {row.dimension for row in repo.point_scores} == {"AI基础认知", "AI伦理与合规"}
    assert {row.score for row in repo.point_scores} == {60.0, 90.0}
    assert all(row.question_count == 1 for row in repo.dimension_scores)


def test_finish_averages_points_inside_one_dimension():
    # 同一维度两道题，考察点部分重叠：重合的考察点取平均，维度再对考察点取平均。
    class PointsScoringAgent(FakeAgent):
        """按考察点给分，避免随机出题顺序影响断言。"""

        async def score(self, request):
            self.scored.append(request)
            score = 90.0 if "AI能力边界认知" in request.assessment_points else 60.0
            return ScoreResponse(score=score, reason="脚本分数", evidence="原话", confidence=0.5)

    repo = FakeRepo([
        question(11, tags=["AI基础认知"], points=["AI基本概念理解"]),
        question(12, tags=["AI基础认知"], points=["AI基本概念理解", "AI能力边界认知"]),
    ])
    flow = build_flow(PointsScoringAgent(action=NEXT_QUESTION), repo)
    run(flow, 1, 7, "")
    run(flow, 1, 7, "回答一")
    run(flow, 1, 7, "回答二")

    points = {row.assessment_point: row.score for row in repo.point_scores}
    assert points == {"AI基本概念理解": 75.0, "AI能力边界认知": 90.0}
    dimension = repo.dimension_scores[0]
    assert dimension.dimension == "AI基础认知"
    assert dimension.score == 82.5                     # (75 + 90) / 2
    assert dimension.question_count == 2
    assert repo.level == {"average_score": 82.5, "ability_level": "L4"}


def test_scoring_failure_is_excluded_from_aggregation():
    class FlakyAgent(SequencedAgent):
        def __init__(self):
            super().__init__([70.0])

        async def score(self, request):
            if self.scored:
                raise RuntimeError("model down")
            return await super().score(request)

    repo = FakeRepo([question(11, tags=["AI基础认知"], points=["AI基本概念理解"]), question(12, tags=["AI伦理与合规"], points=["隐私保护意识"])])
    flow = build_flow(FlakyAgent(), repo)
    run(flow, 1, 7, "")
    run(flow, 1, 7, "回答一")
    run(flow, 1, 7, "回答二")

    # 只有评分成功的那道题进入聚合，失败的那道不产生 0 分，也没有维度行
    assert len(repo.dimension_scores) == 1
    assert len(repo.point_scores) == 1
    assert repo.assessment["status"] == "completed_with_scoring_failure"


def test_questions_without_points_still_fill_their_dimension():
    repo = FakeRepo([question(11, tags=["提示词工程"], points=[])])
    flow = build_flow(SequencedAgent([64.0]), repo)
    run(flow, 1, 7, "")
    run(flow, 1, 7, "回答")

    assert repo.point_scores == []
    assert [(row.dimension, row.score) for row in repo.dimension_scores] == [("提示词工程", 64.0)]
    assert repo.level == {"average_score": 64.0, "ability_level": "L2"}


def test_finishing_twice_does_not_double_the_scores():
    """重复收尾（例如学生连点「结束测评」）：流程跳过二次收尾，写库侧也用 upsert 兜底。"""
    repo = FakeRepo([question(11, tags=["AI基础认知"], points=["AI基本概念理解"])])
    flow = build_flow(SequencedAgent([80.0]), repo)
    run(flow, 1, 7, "")
    run(flow, 1, 7, "回答")

    first = list(repo.dimension_scores)
    anyio.run(lambda: flow.complete(1, 7))

    assert repo.assessment["status"] == "completed"
    assert repo.dimension_scores == first
    assert repo.level == {"average_score": 80.0, "ability_level": "L4"}


def test_a_multi_dimension_question_fills_every_dimension_it_touches():
    repo = FakeRepo([
        question(11, tags=["提示词工程", "AI结果评估与优化"], points=["提示词书写", "评估AI结果"]),
    ])
    flow = build_flow(SequencedAgent([70.0]), repo)
    run(flow, 1, 7, "")
    run(flow, 1, 7, "回答")

    assert {row.dimension: row.score for row in repo.dimension_scores} == {
        "提示词工程": 70.0,
        "AI结果评估与优化": 70.0,
    }
    assert repo.level == {"average_score": 70.0, "ability_level": "L3"}


def test_finish_writes_advice_and_class_profile():
    """收尾时写学习建议与个人班级画像：画像只保留最新一次测评的分数与等级。"""
    repo = FakeRepo([
        question(11, tags=["AI基础认知"], points=["AI基本概念理解"]),
        question(12, tags=["AI伦理与合规"], points=["隐私保护意识"]),
    ])
    flow = build_flow(SequencedAgent([60.0, 90.0]), repo)
    run(flow, 1, 7, "")
    run(flow, 1, 7, "回答一")
    run(flow, 1, 7, "回答二")

    # 建议由聚合结果生成：指出最强的维度、并给出待提升维度的方向
    assert repo.advice
    assert "AI伦理与合规" in repo.advice
    assert repo.profile == {
        "class_id": 1,
        "student_user_id": 7,
        "assessment_id": 1,
        "average_score": 75.0,
        "ability_level": "L3",
    }


def test_advice_can_be_replaced_by_a_custom_writer():
    class FixedAdvice:
        name = "fixed"

        def write(self, aggregation):
            return "固定建议"

    repo = FakeRepo([question(11, tags=["AI基础认知"], points=["AI基本概念理解"])])
    flow = build_flow(SequencedAgent([80.0]), repo, advice_writer=FixedAdvice())
    run(flow, 1, 7, "")
    run(flow, 1, 7, "回答")

    assert repo.advice == "固定建议"


def test_question_count_falls_back_to_the_assessment_when_there_is_no_task():
    """自主练习没有 task，题量上限取学生开始测评时选的 question_count。"""
    repo = FakeRepo([question(11), question(12)], assessment={"question_count": 1})
    flow = build_flow(SequencedAgent([80.0]), repo)
    events = run(flow, 1, 7, "")

    # 只出一道题就要收尾：question_count = 1
    assert [name for name, _ in events] == ["question", "done"]

    run(flow, 1, 7, "回答")

    assert repo.assessment["status"] == "completed"


def test_result_exposes_dimension_scores_points_and_advice():
    repo = FakeRepo([question(11, tags=["AI基础认知"], points=["AI基本概念理解"])])
    flow = build_flow(SequencedAgent([88.0]), repo)
    run(flow, 1, 7, "")
    run(flow, 1, 7, "回答")

    result = anyio.run(lambda: flow.result(1, 7))

    assert result["dimensions"] == [
        {"dimension": "AI基础认知", "score": 88.0, "questionCount": 1}
    ]
    assert result["points"] == [
        {
            "dimension": "AI基础认知",
            "assessmentPoint": "AI基本概念理解",
            "score": 88.0,
            "questionCount": 1,
        }
    ]
    assert result["advice"] == repo.advice
