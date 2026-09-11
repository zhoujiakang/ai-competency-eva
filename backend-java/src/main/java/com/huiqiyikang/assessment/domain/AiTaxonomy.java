package com.huiqiyikang.assessment.domain;

import java.util.List;

/**
 * 维度与考察点的统一校验入口。
 *
 * 三处用到同一套规则，所以只写一遍：出题、教师发布任务、学生开始自主测评。
 * 空集合表示"不限制范围"，退回使用班级全部题库。
 */
public final class AiTaxonomy {
    private AiTaxonomy() {
    }

    /** 校验失败抛 {@link IllegalArgumentException}，消息可直接展示给用户。 */
    public static void validate(List<String> dimensions, List<String> points) {
        if (dimensions == null || dimensions.isEmpty()) {
            if (points != null && !points.isEmpty()) throw new IllegalArgumentException("请先选择维度，再选择考察点");
            return;
        }
        List<AiDimension> known = dimensions.stream()
                .map(d -> AiDimension.byLabel(d).orElseThrow(() -> new IllegalArgumentException("维度不在固定分类内：" + d)))
                .toList();
        if (points == null) return;
        for (String label : points) {
            AiAssessmentPoint point = AiAssessmentPoint.byLabel(label)
                    .orElseThrow(() -> new IllegalArgumentException("考察点不在固定分类内：" + label));
            if (!known.contains(point.dimension()))
                throw new IllegalArgumentException("考察点「" + point.label() + "」不属于所选维度");
        }
    }
}
