package com.huiqiyikang.assessment.profile;

import com.huiqiyikang.assessment.domain.AbilityLevelScale;
import com.huiqiyikang.assessment.mapper.AssessmentDimensionScoreRepository;
import com.huiqiyikang.assessment.mapper.AssessmentPointScoreRepository;
import com.huiqiyikang.assessment.mapper.AssessmentRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * 把数据库里的材料装进 {@link AbilityProfileContext}。
 *
 * 查询只做一次（该班级下该学生最近 N 次已完成测评），维度分与考察点分由上下文按需惰性查询，
 * 所以像「加权最近三次」这种只碰少量测评的算法不会把整段历史都读出来。
 *
 * 历史条数由 app.ability-profile.history-limit 控制（默认 20）。它只影响策略能看到多少历史，
 * 不影响最新一次的口径——调大它不会改变默认策略的结果。
 */
@Component
public class AbilityProfileContextLoader {

    public static final int DEFAULT_HISTORY_LIMIT = 20;

    private final AssessmentRepository assessments;
    private final AssessmentDimensionScoreRepository dimensions;
    private final AssessmentPointScoreRepository points;
    private final AbilityLevelScale levelScale;
    private final int historyLimit;

    public AbilityProfileContextLoader(
            AssessmentRepository assessments,
            AssessmentDimensionScoreRepository dimensions,
            AssessmentPointScoreRepository points,
            AbilityLevelScale levelScale,
            @Value("${app.ability-profile.history-limit:" + DEFAULT_HISTORY_LIMIT + "}") int historyLimit) {
        this.assessments = assessments;
        this.dimensions = dimensions;
        this.points = points;
        this.levelScale = levelScale;
        this.historyLimit = Math.max(1, historyLimit);
    }

    public AbilityProfileContext load(Long classId, Long studentUserId) {
        return new AbilityProfileContext(
                classId,
                studentUserId,
                assessments.findRecentCompleted(classId, studentUserId, historyLimit),
                levelScale,
                dimensions,
                points);
    }
}
