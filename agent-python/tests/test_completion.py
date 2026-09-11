"""收尾的确定性规则：学生要跳过、或本题问得太多轮，就必须结束，不给模型裁量。"""

import pytest

from app.agent.actions import NEXT_QUESTION
from app.agent.completion import SKIP_MAX_CHARS, forced_action, wants_to_skip
from app.domain.schemas import Message


@pytest.mark.parametrize(
    "text",
    ["直接下一题", "这题我不会，直接下一题即可", "继续下一题，这题给我0分即可", "不要这题了，下一题", "跳过这题", "换一题吧"],
)
def test_student_can_always_end_a_topic(text):
    """回归测试：学生说"下一题"就一定要能翻篇，不能被反复追问困住。"""
    assert wants_to_skip([Message(sender_type="student", content=text)]) is True


@pytest.mark.parametrize(
    "text",
    [
        "我会先确认目标读者和输出格式，再看数据来源是否可靠。",
        "我不会忘记在动手前先核对需求，这一点我上一轮说过。",
        "在我们团队，遇到分歧会先对齐事实，再讨论方案。",
    ],
)
def test_normal_answers_are_not_treated_as_skipping(text):
    assert wants_to_skip([Message(sender_type="student", content=text)]) is False


def test_only_the_students_latest_message_counts():
    history = [
        Message(sender_type="student", content="下一题"),
        Message(sender_type="ai", content="好，这题我们先过。"),
        Message(sender_type="student", content="我重新说一下我的思路：先对齐目标再验证。"),
    ]
    assert wants_to_skip(history) is False


def test_a_very_long_message_is_never_treated_as_skipping():
    """正常作答里偶然出现"跳过"两个字，不能因为超长文本被判成跳过。"""
    text = "跳过" + "补充" * (SKIP_MAX_CHARS // 2)
    assert wants_to_skip([Message(sender_type="student", content=text)]) is False


def test_skip_phrase_forces_next_question():
    history = [Message(sender_type="student", content="这题我不会，直接下一题")]
    assert forced_action(history, turn_count=1, max_turns=6) == NEXT_QUESTION


def test_turn_limit_forces_next_question():
    history = [Message(sender_type="student", content="我再补充一点依据。")]
    assert forced_action(history, turn_count=6, max_turns=6) == NEXT_QUESTION


def test_ordinary_answers_leave_the_decision_to_the_agent():
    history = [Message(sender_type="student", content="我先对齐目标，再验证数据来源。")]
    assert forced_action(history, turn_count=1, max_turns=6) is None


def test_zero_max_turns_means_no_limit():
    """max_topic_turns=0 表示不限制轮次（和出题引擎 question_count=0 的语义一致）。"""
    history = [Message(sender_type="student", content="我再补充一点依据。")]
    assert forced_action(history, turn_count=99, max_turns=0) is None
