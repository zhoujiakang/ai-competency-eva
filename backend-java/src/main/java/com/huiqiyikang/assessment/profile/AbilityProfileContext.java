package com.huiqiyikang.assessment.profile;

import com.huiqiyikang.assessment.domain.AbilityLevelScale;
import com.huiqiyikang.assessment.entity.Assessment;
import com.huiqiyikang.assessment.mapper.AssessmentDimensionScoreRepository;
import com.huiqiyikang.assessment.mapper.AssessmentPointScoreRepository;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 画像策略的输入：一个学生在一个班级下的全部原始材料。
 *
 * 这个类只负责「把材料摆好」，不包含任何算法——算法是
 * {@link AbilityProfileStrategy#build(AbilityProfileContext)} 的事。
 * 想换算法的人只需要关心这里能拿到什么。
 *
 * 提供的东西：
 *   · 班级与学生：classId() / studentUserId()
 *   · 历史测评：history()，该班级下该学生**已完成的**测评，按完成时间倒序，[0] 是最新一次
 *   · 分数明细：dimensionsOf(assessmentId) / pointsOf(assessmentId)，按需查询并缓存
 *   · 共用口径：averageScoreOf() / summaryOf()，等级划档统一走 AbilityLevelScale
 *
 * 历史条数由 app.ability-profile.history-limit 控制（默认 20），避免把整张表读进来。
 */
public final class AbilityProfileContext {

    private final Long classId;
    private final Long studentUserId;
    private final List<Assessment> history;
    private final AbilityLevelScale levelScale;
    private final AssessmentDimensionScoreRepository dimensionRepository;
    private final AssessmentPointScoreRepository pointRepository;

    // 一次请求内同一份分数只查一次：策略可能反复取同一个 assessmentId 的明细
    private final Map<Long, List<AbilityProfile.DimensionScore>> dimensionCache = new HashMap<>();
    private final Map<Long, List<AbilityProfile.PointScore>> pointCache = new HashMap<>();

    public AbilityProfileContext(
            Long classId,
            Long studentUserId,
            List<Assessment> history,
            AbilityLevelScale levelScale,
            AssessmentDimensionScoreRepository dimensionRepository,
            AssessmentPointScoreRepository pointRepository) {
        this.classId = classId;
        this.studentUserId = studentUserId;
        this.history = List.copyOf(history);
        this.levelScale = levelScale;
        this.dimensionRepository = dimensionRepository;
        this.pointRepository = pointRepository;
    }

    public Long classId() {
        return classId;
    }

    public Long studentUserId() {
        return studentUserId;
    }

    /** 已完成的测评，按完成时间倒序；[0] 是最新一次。可能为空。 */
    public List<Assessment> history() {
        return history;
    }

    public boolean hasAssessment() {
        return !history.isEmpty();
    }

    public AbilityLevelScale levelScale() {
        return levelScale;
    }

    /** 某次测评的六维分。 */
    public List<AbilityProfile.DimensionScore> dimensionsOf(Long assessmentId) {
        return dimensionCache.computeIfAbsent(assessmentId, id -> {
            List<AbilityProfile.DimensionScore> rows = new ArrayList<>();
            dimensionRepository.findByAssessmentId(id).forEach(row ->
                    rows.add(new AbilityProfile.DimensionScore(
                            row.getDimension(), row.getScore(), row.getQuestionCount())));
            return List.copyOf(rows);
        });
    }

    /** 某次测评的考察点分（技能树的数据源）。 */
    public List<AbilityProfile.PointScore> pointsOf(Long assessmentId) {
        return pointCache.computeIfAbsent(assessmentId, id -> {
            List<AbilityProfile.PointScore> rows = new ArrayList<>();
            pointRepository.findByAssessmentId(id).forEach(row ->
                    rows.add(new AbilityProfile.PointScore(
                            row.getDimension(), row.getAssessmentPoint(),
                            row.getScore(), row.getQuestionCount())));
            return List.copyOf(rows);
        });
    }

    /**
     * 综合分口径：优先用 Agent 收尾时写好的 average_score（六维分的平均），
     * 历史数据没有这一列时回退到 total_score（所有题目分的平均）。
     */
    public Double averageScoreOf(Assessment assessment) {
        return assessment.getAverageScore() != null ? assessment.getAverageScore() : assessment.getTotalScore();
    }

    /** 把一次测评转成画像摘要；等级优先用落库的，缺失时按分数现算。 */
    public AbilityProfile.Summary summaryOf(Assessment assessment) {
        AbilityLevelScale.Level level = levelScale.resolve(assessment.getAbilityLevel(), averageScoreOf(assessment));
        return new AbilityProfile.Summary(
                assessment.getId(),
                averageScoreOf(assessment),
                level.code(),
                level.name(),
                assessment.getCompletedAt());
    }
}
