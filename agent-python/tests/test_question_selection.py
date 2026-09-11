"""出题引擎的行为：换不换题、换哪道、什么时候收尾。

策略本身还没定，所以这里只钉住不能破的边界：不重复出题、不超出考察范围
（范围内没有时退回全部题库）、当前题没问完就不换。
"""

import random

import pytest

from app.tools.question_selection import QuestionEngine, RandomEngine, eligible_candidates
from tests.support import candidate, engine_context


def test_continues_the_current_question_until_it_is_finished():
    engine = QuestionEngine()
    context = engine_context([candidate(1), candidate(2)], current=candidate(1), current_finished=False)
    assert engine.decide(context).action == "continue"


def test_switches_to_an_unused_question_once_the_current_one_is_finished():
    engine = QuestionEngine(RandomEngine(random.Random(7)))
    picks = {
        engine.decide(engine_context(
            [candidate(1), candidate(2), candidate(3)],
            used={1},
            current=candidate(1),
            current_finished=True,
        )).question.id
        for _ in range(50)
    }
    assert picks == {2, 3}


def test_finishes_when_every_question_has_been_used():
    engine = QuestionEngine()
    decision = engine.decide(engine_context([candidate(1), candidate(2)], used={1, 2}))
    assert decision.action == "finish"


def test_finishes_when_the_expected_question_count_is_reached():
    engine = QuestionEngine()
    decision = engine.decide(engine_context(
        [candidate(1), candidate(2), candidate(3)],
        used={1, 2},
        question_count=2,
        completed_count=2,
    ))
    assert decision.action == "finish"
    assert "题数上限" in decision.reason


def test_only_questions_inside_the_selected_scope_can_be_picked():
    engine = QuestionEngine(RandomEngine(random.Random(1)))
    context = engine_context(
        [candidate(1, tags=["AI基础认知"]), candidate(2, tags=["AI伦理与合规"])],
        dimensions=["AI伦理与合规"],
    )
    assert {engine.decide(context).question.id for _ in range(30)} == {2}


def test_scope_is_ignored_when_nothing_matches_so_the_run_never_gets_stuck():
    engine = QuestionEngine(RandomEngine(random.Random(1)))
    context = engine_context([candidate(1, tags=["AI基础认知"])], dimensions=["AI伦理与合规"])
    assert engine.decide(context).action == "switch"
    assert eligible_candidates(context)[0].id == 1


def test_a_replacement_strategy_receives_the_full_context():
    seen = {}

    class ByPoint:
        name = "by-point"

        def decide(self, context):
            from app.tools.question_selection import Decision

            seen["dimensions"] = context.dimensions
            seen["used"] = set(context.used_question_ids)
            seen["progress"] = (context.completed_count, context.question_count)
            return Decision("switch", context.candidates[0], "由测试策略选择")

    engine = QuestionEngine(ByPoint())
    decision = engine.decide(engine_context(
        [candidate(1)],
        used={9},
        dimensions=["提示词工程"],
        question_count=3,
        completed_count=1,
    ))

    assert decision.question.id == 1
    assert seen == {"dimensions": ("提示词工程",), "used": {9}, "progress": (1, 3)}


def test_seeded_rng_makes_the_engine_reproducible():
    first = QuestionEngine(RandomEngine(random.Random(7)))
    second = QuestionEngine(RandomEngine(random.Random(7)))
    picks_first = [first.decide(engine_context([candidate(i) for i in range(1, 6)])).question.id for _ in range(10)]
    picks_second = [second.decide(engine_context([candidate(i) for i in range(1, 6)])).question.id for _ in range(10)]
    assert picks_first == picks_second


def test_empty_bank_ends_the_assessment_instead_of_raising():
    """题库为空时引擎给出收尾结论，由流程决定怎么结束，而不是抛异常。"""
    decision = QuestionEngine(RandomEngine(random.Random(1))).decide(engine_context([]))
    assert decision.action == "finish"
