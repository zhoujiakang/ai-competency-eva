package com.huiqiyikang.assessment.profile;

import java.time.Instant;
import java.util.List;

/**
 * 用户能力画像：一个「学生 × 班级」在当前算法下的能力画像。
 *
 * 这是画像模块对外的唯一形状，接口直接把它序列化出去，所以字段名就是接口契约
 * （前端读 `hasAssessment` / `latest` / `dimensions` / `points` / `trend` / `previous`）。
 *
 * 注意「画像」与「一次测评」的区别：画像是对一个人在该班级下的能力评价，
 * 由 {@link AbilityProfileStrategy} 决定用哪些测评、怎么算出这些分数。
 * 默认算法是「取最新一次测评」，换成别的算法不需要改任何调用方。
 */
public record AbilityProfile(
        Long classId,
        boolean hasAssessment,
        Summary latest,
        List<DimensionScore> dimensions,
        List<PointScore> points,
        List<Summary> trend,
        Previous previous) {

    /** 一次测评的画像摘要：综合分 + 等级 + 完成时间。 */
    public record Summary(
            Long assessmentId,
            Double averageScore,
            String level,
            String levelName,
            Instant completedAt) {
    }

    /** 上一次测评：摘要 + 它自己的六维分（前端做「与上一次对比」）。 */
    public record Previous(
            Long assessmentId,
            Double averageScore,
            String level,
            String levelName,
            Instant completedAt,
            List<DimensionScore> dimensions) {
    }

    public record DimensionScore(String dimension, Double score, Integer questionCount) {
    }

    public record PointScore(String dimension, String assessmentPoint, Double score, Integer questionCount) {
    }

    /** 该班级下还没有测评时的空画像：前端据此显示 L0 空状态。 */
    public static AbilityProfile empty(Long classId) {
        return new AbilityProfile(classId, false, null, List.of(), List.of(), List.of(), null);
    }
}
