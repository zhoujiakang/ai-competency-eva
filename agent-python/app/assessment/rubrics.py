"""题目快照 → 喂给模型的「评分关注点」文本。

同一个题目快照要拼成两段不同的话，分别给两个环节用：

    dialogue_rubric  对话环节：告诉模型这是个带参考选项的开放问题，
                     学生可以用自己的话回答，请围绕当前问题自然追问
    scoring_rubric   评分环节：给出明确的评分依据；题目没写评分标准时，
                     用「参考选项 + 标准答案」拼一段兜底说明

两者都会附上本题考察点（points_clause）。拼文案是纯函数，不碰数据库也不调模型。
"""

from __future__ import annotations

from app.db.repository import load_list


def dialogue_rubric(question: dict) -> str:
    options = question.get("options_snapshot") or "未提供"
    rubric = (question.get("rubric_snapshot") or "").strip() or "围绕回答的依据、推理、边界条件和个人见解进行判断"
    return (
        rubric
        + "。这是一个带参考选项的开放式问题，参考选项为：" + options
        + "。学生可以选择某个选项，也可以用自己的话解释、补充理由、提出例外情况或新的见解。"
        + "请围绕当前问题自然追问，不要要求学生只能发送选项字母。"
        + points_clause(question)
    )


def scoring_rubric(question: dict) -> str:
    rubric = (question.get("rubric_snapshot") or "").strip()
    if rubric:
        return rubric + points_clause(question)
    return (
        "这是一个带参考选项的开放式作答题。参考选项为："
        + (question.get("options_snapshot") or "未提供")
        + "；标准答案为：" + (question.get("answer_snapshot") or "未提供")
        + "。评价时既要考虑结论是否合理，也要考虑学生是否提供了自己的解释、依据和见解。"
        + points_clause(question)
    )


def points_clause(question: dict) -> str:
    points = load_list(question.get("assessment_points_snapshot"))
    return f"本主题考察点：{'、'.join(points)}。" if points else ""
