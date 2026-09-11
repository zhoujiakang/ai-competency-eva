package com.huiqiyikang.assessment.domain;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 词表规则（《具体考察点2.0》）：
 * 6 个维度 / 20 个考察点；维度可多选；使用场景不再是考察点。
 */
class AiTaxonomyTest {

    @Test
    void sixDimensionsAndTwentyPointsEachWithADescription() {
        assertEquals(6, AiDimension.values().length);
        assertEquals(20, AiAssessmentPoint.values().length);
        for (AiDimension dimension : AiDimension.values()) {
            List<AiAssessmentPoint> points = AiAssessmentPoint.of(dimension);
            assertFalse(points.isEmpty(), dimension.label() + " 应该有考察点");
            for (AiAssessmentPoint point : points) {
                assertFalse(point.description().isBlank(), point.label() + " 应该有介绍");
            }
        }
        assertEquals(4, AiAssessmentPoint.of(AiDimension.AI_TOOL_USAGE).size());
    }

    @Test
    void useScenariosAreNoLongerAssessmentPoints() {
        // 8 个场景（文本写作 / 编程开发 …）不再单独成点
        assertTrue(AiAssessmentPoint.byLabel("编程开发").isEmpty());
        assertTrue(AiAssessmentPoint.byLabel("文本写作").isEmpty());
        assertTrue(AiAssessmentPoint.byLabel("工具使用能力：编程开发").isEmpty());
    }

    @Test
    void toolUsageScenariosAreMergedIntoTheirPointDescription() {
        String selection = AiAssessmentPoint.TOOL_SELECTION_AND_LIMITS.description();
        for (String scenario : List.of("文本写作", "图像生成", "视频制作", "音频处理",
                "设计辅助", "办公与写作", "编程开发", "数据分析与商业智能")) {
            assertTrue(selection.contains(scenario), "工具选型及局限性认知 应该包含场景：" + scenario);
        }
        String skill = AiAssessmentPoint.TOOL_USAGE_SKILL.description();
        for (String scenario : List.of("文本写作", "编程开发", "数据分析与商业智能")) {
            assertTrue(skill.contains(scenario), "工具使用能力 应该包含场景：" + scenario);
        }
        // 工作流整合 / 智能体编排 的场景被丢弃，只留一段描述
        assertFalse(AiAssessmentPoint.WORKFLOW_INTEGRATION.description().contains("文本写作"));
        assertFalse(AiAssessmentPoint.AGENT_ORCHESTRATION.description().contains("文本写作"));
    }

    @Test
    void aQuestionCanBelongToSeveralDimensions() {
        assertDoesNotThrow(() -> AiTaxonomy.validate(
                List.of("提示词工程", "AI结果评估与优化"),
                List.of("提示词书写", "评估AI结果")));
    }

    @Test
    void pointMustBelongToOneOfTheSelectedDimensions() {
        IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
                () -> AiTaxonomy.validate(List.of("提示词工程"), List.of("评估AI结果")));
        assertTrue(error.getMessage().contains("不属于所选维度"));
    }

    @Test
    void unknownValuesAreRejected() {
        assertThrows(IllegalArgumentException.class,
                () -> AiTaxonomy.validate(List.of("不存在的维度"), List.of()));
        assertThrows(IllegalArgumentException.class,
                () -> AiTaxonomy.validate(List.of("提示词工程"), List.of("不存在的考察点")));
        assertThrows(IllegalArgumentException.class,
                () -> AiTaxonomy.validate(List.of("AI工具使用"), List.of("编程开发")));
    }
}
