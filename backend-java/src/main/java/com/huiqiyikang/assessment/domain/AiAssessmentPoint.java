package com.huiqiyikang.assessment.domain;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

/**
 * 具体考察点（二级分类），每个考察点固定归属一个 {@link AiDimension}。
 *
 * 来源：《具体考察点2.0》。共 6 个维度 / 20 个考察点，考察点是技能树的节点单位，
 * 也是「AI 能力标准」页和实操任务评分参考的落点。
 *
 * 关于「AI工具使用」这个维度：文档里它下面还铺了一层使用场景
 * （文本写作 / 图像生成 / 视频制作 / 音频处理 / 设计辅助 / 办公与写作 / 编程开发 /
 * 数据分析与商业智能）。场景**不作为考察点**——它们连同各自的描述被拼进所属考察点的
 * 介绍里，所以词表的第二级仍然是这 4 个考察点。
 *
 * description 里用 {@code \n} 分行（编号关注点一行一条），前端按 pre-line 展示。
 *
 * 数据库里存 {@link #label()}（中文名）而不是枚举名，保证历史数据和导出结果可读。
 */
public enum AiAssessmentPoint {
    // ---------------------------------------------------------------- AI基础认知（7）
    AI_BASIC_CONCEPTS(AiDimension.AI_FOUNDATION, "AI基本概念理解",
            "能准确区分AI、机器学习、深度学习、大语言模型等核心概念及其关系；能用通俗语言向非专业人士解释这些概念"),
    DATA_INFLUENCES_AI_OUTPUT(AiDimension.AI_FOUNDATION, "数据影响AI输出的认知",
            "能说明训练数据中的偏差如何导致AI输出偏误；能举例说明数据质量（完整性、代表性、时效性）对AI生成内容准确性的影响"),
    AI_DECISION_LOGIC(AiDimension.AI_FOUNDATION, "AI决策的基本逻辑",
            "能理解AI系统基于数据和概率做出决策的基本逻辑；能区分基于规则的系统与基于学习的系统的差异"),
    AI_HISTORY(AiDimension.AI_FOUNDATION, "AI发展历程认知",
            "能概述AI发展的重要里程碑（如图灵测试、深度学习突破、大语言模型兴起等）；能理解当前生成式AI的技术定位"),
    AI_CAPABILITY_BOUNDARY(AiDimension.AI_FOUNDATION, "AI能力边界认知",
            "能准确说明AI擅长什么、不擅长什么；能识别AI的局限性（如缺乏真正的理解力、常识推理能力有限、依赖训练数据分布等）"),
    AI_SOCIAL_IMPACT(AiDimension.AI_FOUNDATION, "AI社会影响认知",
            "能分析AI对就业、教育、信息传播、社会公平等领域的影响；能讨论AI带来的机遇与挑战"),
    CRITICAL_VIEW_OF_AI(AiDimension.AI_FOUNDATION, "批判性看待AI",
            "能对AI输出保持审慎态度，不盲目信任；能从技术、伦理、社会等多维度批判性评估AI的应用"),

    // ---------------------------------------------------------------- 提示词工程（1）
    PROMPT_WRITING(AiDimension.PROMPT_ENGINEERING, "提示词书写",
            "1.角色设定：明确设定了AI的角色身份（如“你是一名资深数据分析师”）\n"
            + "2.任务描述及拆解：清晰说明了要完成什么任务、目标是什么；将复杂任务合理拆解为多个可执行的子任务\n"
            + "3.上下文提供：提供了足够的背景信息让AI理解任务场景\n"
            + "4.约束条件：明确了输出格式、长度、风格等约束\n"
            + "5.少样本示例：提供了2-5个高质量的输入-输出示例\n"
            + "6.思维链引导：引导AI进行分步推理（如“请逐步思考”）\n"
            + "7.指令清晰度：指令具体、无歧义，避免模糊表达\n"
            + "8.语言质量：语法正确、表达流畅"),

    // ---------------------------------------------------------------- AI工具使用（4）
    // 这 4 个考察点下的 8 个使用场景不单独成点：场景名与描述按行拼进介绍里。
    TOOL_SELECTION_AND_LIMITS(AiDimension.AI_TOOL_USAGE, "工具选型及局限性认知",
            "文本写作：能根据任务需求（如文案创作、报告撰写、邮件起草等）选择合适的AI写作工具；能识别不同工具在语言风格、专业领域、输出质量上的差异与局限\n"
            + "图像生成：能根据视觉需求（如插画、海报、产品设计草图等）选择合适的AI图像生成工具；能理解不同模型在风格、分辨率、可控性上的差异\n"
            + "视频制作：能根据视频创作需求选择合适的AI视频工具；能理解当前AI视频生成在时长、连贯性、物理规律模拟等方面的局限性\n"
            + "音频处理：能根据音频需求（如语音合成、音乐生成、音频编辑等）选择合适的AI音频工具\n"
            + "设计辅助：能根据设计需求（如UI设计、平面设计、3D建模等）选择合适的AI设计辅助工具\n"
            + "办公与写作：能根据办公场景（如PPT制作、数据分析报告、会议纪要等）选择合适的AI办公工具\n"
            + "编程开发：能根据编程任务（如代码补全、Debug、代码重构等）选择合适的AI编程助手；能理解不同工具在语言支持、上下文理解深度上的差异\n"
            + "数据分析与商业智能：能根据数据分析需求（如数据清洗、可视化、预测建模等）选择合适的AI分析工具"),

    TOOL_USAGE_SKILL(AiDimension.AI_TOOL_USAGE, "工具使用能力",
            "文本写作：能熟练使用AI写作工具完成高质量文本生成；能通过提示词精确控制输出风格、结构和长度\n"
            + "图像生成：能熟练使用AI图像生成工具；能通过详细的描述、参考图像或风格要求确保生成结果符合预期\n"
            + "视频制作：能使用AI视频工具完成基础视频创作（如脚本生成、自动剪辑、字幕生成等）\n"
            + "音频处理：能使用AI音频工具完成基础音频处理任务\n"
            + "设计辅助：能使用AI设计工具完成基础设计任务\n"
            + "办公与写作：能使用AI办公工具提升日常工作效率（如文档处理、数据整理、演示文稿制作等）\n"
            + "编程开发：能使用AI编程助手提升代码开发效率和质量\n"
            + "数据分析与商业智能：能使用AI分析工具完成数据探索、可视化和基础建模"),

    // 下面两个考察点在文档里没有场景差异，8 行场景只有第一行有内容，因此直接收敛成一段描述。
    WORKFLOW_INTEGRATION(AiDimension.AI_TOOL_USAGE, "工作流整合",
            "能将AI工具系统性地嵌入日常工作流程中，形成“人-AI”协作的常态化工作模式；能识别工作流中哪些环节适合AI介入、哪些环节需要人工主导"),
    AGENT_ORCHESTRATION(AiDimension.AI_TOOL_USAGE, "智能体编排",
            "能理解智能体（Agent）的基本概念和工作原理；能编排多个智能体完成复杂任务（如一个智能体负责信息检索、一个负责内容生成、一个负责质量校验）；能设定智能体间的协作规则和交接机制"),

    // ---------------------------------------------------------------- AI结果评估与优化（2）
    EVALUATE_AI_OUTPUT(AiDimension.AI_OUTPUT_EVALUATION, "评估AI结果",
            "1.事实核查：主动核验AI输出中的事实性信息（数据、日期、引用等）\n"
            + "2.幻觉识别：能识别AI生成的“看似合理但错误”的内容\n"
            + "3.偏见察觉：能识别AI输出中的刻板印象或系统性偏见\n"
            + "4.指令遵循验证：能判断AI是否严格遵循了原始指令"),
    OPTIMIZE_AI_OUTPUT(AiDimension.AI_OUTPUT_EVALUATION, "优化AI结果",
            "1.优化指令能力：能针对发现的问题写出具体的改进指令（而非“再改改”）\n"
            + "2.迭代优化意识：主动进行多轮对话来逐步逼近理想输出"),

    // ---------------------------------------------------------------- 人机协同解决问题（1）
    COLLABORATIVE_PROBLEM_SOLVING(AiDimension.HUMAN_AI_COLLABORATION, "与AI协作解决问题",
            "1.任务拆解：将复杂任务合理拆解为多个可执行的子任务\n"
            + "2.AI调用时机：在合适的环节调用AI（而非全程依赖或完全不使用）\n"
            + "3.提问能力：向AI提问具体、有针对性\n"
            + "4.认知评估：对AI提供的信息进行批判性思考和评估\n"
            + "5.认知反思：反思自己的思路和AI的贡献，调整策略\n"
            + "6.人智适应：能根据AI的反馈灵活调整自己的计划\n"
            + "7.冲突调解：当AI输出与预期不符时，能有效协调解决\n"
            + "8.知识创造：在协同过程中产生了超越人/AI单独工作的新见解"),

    // ---------------------------------------------------------------- AI伦理与合规（5）
    PRIVACY_PROTECTION(AiDimension.AI_ETHICS_COMPLIANCE, "隐私保护意识",
            "在使用AI工具时主动关注数据隐私；不输入敏感个人信息（如身份证号、银行账号、生物特征等）；了解所用AI工具的数据处理政策和存储方式"),
    COMPLIANCE_AWARENESS(AiDimension.AI_ETHICS_COMPLIANCE, "合规意识",
            "了解并遵守所在行业/地区关于AI使用的法律法规（如《数据安全法》《个人信息保护法》、欧盟AI法案等）；能在实际使用中识别并规避合规风险"),
    BIAS_AND_HARMFUL_CONTENT(AiDimension.AI_ETHICS_COMPLIANCE, "偏见及有害内容识别",
            "能识别AI输出中的性别、种族、年龄、地域等刻板印象和系统性偏见；能识别并拒绝生成或传播仇恨、歧视、暴力等有害内容；能主动核查AI输出中是否存在代表性缺失或价值观偏差"),
    COPYRIGHT_AND_IP(AiDimension.AI_ETHICS_COMPLIANCE, "版权与知识产权认知",
            "了解AI生成内容的版权归属问题；能区分使用AI辅助创作与完全依赖AI生成在知识产权上的不同；在使用AI生成内容时能正确标注来源并遵守相关版权规定"),
    ACCOUNTABILITY(AiDimension.AI_ETHICS_COMPLIANCE, "问责意识",
            "清楚AI工具的使用者（而非AI本身）应对最终结果负责；能在AI辅助决策中保持人类的主导权和最终判断权");

    private final AiDimension dimension;
    private final String name;
    private final String description;

    AiAssessmentPoint(AiDimension dimension, String name, String description) {
        this.dimension = dimension;
        this.name = name;
        this.description = description;
    }

    public AiDimension dimension() {
        return dimension;
    }

    /** 考察点自身的中文名，例如「工具使用能力」。 */
    public String pointName() {
        return name;
    }

    /** 考察点介绍（来自《具体考察点2.0》），前端「AI 能力标准」页与评分参考都用它。 */
    public String description() {
        return description;
    }

    /** 落库和前端展示用的名字。20 个考察点名字全局唯一。 */
    public String label() {
        return name;
    }

    /** 某个维度下的全部考察点。 */
    public static List<AiAssessmentPoint> of(AiDimension dimension) {
        return Arrays.stream(values()).filter(x -> x.dimension == dimension).toList();
    }

    /** 按完整名字反查；不是受控词表里的值就返回空。 */
    public static Optional<AiAssessmentPoint> byLabel(String label) {
        if (label == null) return Optional.empty();
        String wanted = label.trim();
        return Arrays.stream(values()).filter(x -> x.label().equals(wanted)).findFirst();
    }

    public static boolean isKnown(String label) {
        return byLabel(label).isPresent();
    }
}
