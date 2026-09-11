package com.huiqiyikang.assessment.domain;

import java.util.Arrays;
import java.util.Optional;

/**
 * AI 使用能力的固定维度（一级分类）。
 *
 * 来源：《具体考察点2.0》的「维度」列。这份清单是受控词表：题目的维度必须在这里，
 * 前端只能下拉选择，不接受教师自由输入。
 *
 * 数据库里存 {@link #label()}（中文名）而不是枚举名，保证历史数据和导出结果可读。
 */
public enum AiDimension {
    AI_FOUNDATION("AI基础认知", "理解 AI 的核心概念、决策逻辑、能力边界与社会影响，并能批判性地看待 AI。"),
    PROMPT_ENGINEERING("提示词工程", "编写高质量提示词，用角色、任务、上下文、约束与示例精确控制 AI 的输出。"),
    AI_TOOL_USAGE("AI工具使用", "根据任务选择合适的 AI 工具，熟练使用、融入日常工作流，并能编排智能体完成复杂任务。"),
    AI_OUTPUT_EVALUATION("AI结果评估与优化", "核查 AI 输出的事实、幻觉与偏见，并通过多轮迭代把结果改进到理想状态。"),
    HUMAN_AI_COLLABORATION("人机协同解决问题", "合理拆解任务、把握人机分工，在与 AI 的协作中高效解决真实问题。"),
    AI_ETHICS_COMPLIANCE("AI伦理与合规", "关注隐私、合规、偏见、版权与问责，负责任地使用 AI。");

    private final String label;
    private final String description;

    AiDimension(String label, String description) {
        this.label = label;
        this.description = description;
    }

    public String label() {
        return label;
    }

    /** 维度介绍，前端「AI 能力标准」页的维度卡片展示用。 */
    public String description() {
        return description;
    }

    /** 按中文名反查；不是受控词表里的值就返回空。 */
    public static Optional<AiDimension> byLabel(String label) {
        if (label == null) return Optional.empty();
        String wanted = label.trim();
        return Arrays.stream(values()).filter(x -> x.label.equals(wanted)).findFirst();
    }

    public static boolean isKnown(String label) {
        return byLabel(label).isPresent();
    }
}
