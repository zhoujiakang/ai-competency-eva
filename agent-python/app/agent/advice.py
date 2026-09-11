"""学习建议：测评收尾时生成一段写给学生的文字建议。

与 ScoringTool 一样是注入式的：默认实现是规则式的（不调模型、不会失败），
要换成模型生成，实现同样的 ``write()`` 再注入给 AssessmentFlow 即可：

    flow = AssessmentFlow(agent, repo, settings, advice_writer=MyAdviceWriter())

输入是聚合结果（维度分 + 考察点分 + 综合分 + 等级），所以建议与雷达图、
技能树用的是同一份数据，不会出现「图上 82 分、建议里说 60 分」这种矛盾。
"""

from __future__ import annotations

from typing import Protocol

from app.domain.aggregation import Aggregation


# 六个维度各自的提升方向；维度名与词表（AiDimension）一致。
DIMENSION_ADVICE: dict[str, str] = {
    "AI基础认知": "补一补模型的能力边界与决策逻辑，遇到输出先想「它为什么会给出这个结果」",
    "提示词工程": "练习把角色、目标、约束条件和输出格式写全，再对比优化前后的效果",
    "AI工具使用": "按场景挑工具，把 AI 嵌入到完整工作流里，而不只是单点使用",
    "AI结果评估与优化": "养成事实核查的习惯，发现问题的指令要具体到「改什么、改成什么样」",
    "人机协同解决问题": "先拆解任务再决定哪些环节交给 AI，并对它的输出保持复核",
    "AI伦理与合规": "注意隐私、版权与偏见问题，AI 辅助的结论最终由使用者负责",
}

DEFAULT_ADVICE = "多轮练习并复盘自己的回答，是提升最直接的方式"


class AdviceWriter(Protocol):
    """学习建议生成协议。换算法只需要换这个实现。"""

    name: str

    def write(self, aggregation: Aggregation) -> str:
        ...


class RuleBasedAdviceWriter:
    """默认实现：按「优势维度 + 待提升维度」组织一段确定性的建议，不调用模型。"""

    name = "rule"

    def write(self, aggregation: Aggregation) -> str:
        dimensions = [row for row in aggregation.dimensions if row.question_count > 0]
        if not dimensions:
            return "本次测评没有产生有效评分，暂时无法生成学习建议。"

        ordered = sorted(dimensions, key=lambda row: row.score, reverse=True)
        strongest = ordered[0]
        weakest = ordered[-1]
        level = aggregation.level
        average = aggregation.average_score

        parts: list[str] = []
        if average is not None:
            parts.append(f"本次测评综合得分 {average:.1f} 分，当前等级 {level.level} {level.name}。")
        else:
            parts.append(f"本次测评当前等级 {level.level} {level.name}。")

        parts.append(f"表现最好的是「{strongest.dimension}」（{strongest.score:.1f} 分），可以继续保持。")

        if weakest.dimension == strongest.dimension:
            parts.append(f"建议{DEFAULT_ADVICE}。")
            return "".join(parts)

        advice = DIMENSION_ADVICE.get(weakest.dimension, DEFAULT_ADVICE)
        parts.append(f"相对薄弱的是「{weakest.dimension}」（{weakest.score:.1f} 分），建议{advice}。")

        weakest_points = sorted(
            (row for row in aggregation.points if row.dimension == weakest.dimension),
            key=lambda row: row.score,
        )[:2]
        if weakest_points:
            names = "、".join(f"「{row.assessment_point}」" for row in weakest_points)
            parts.append(f"其中可以优先从{names}开始练。")

        return "".join(parts)
