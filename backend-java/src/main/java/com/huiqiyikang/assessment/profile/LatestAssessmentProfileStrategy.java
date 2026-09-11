package com.huiqiyikang.assessment.profile;

import com.huiqiyikang.assessment.entity.Assessment;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * 默认画像算法：取该班级下**最新一次已完成测评**的分数作为当前画像。
 *
 * 这是画像模块的第一版口径，也是改造前 AbilityService 的行为，做到「换架构不换结果」：
 *   · latest / dimensions / points 全部来自最新那一次测评；
 *   · trend 取最近 {@value #TREND_LIMIT} 次测评的综合分，按时间**升序**给折线图用；
 *   · previous 是倒数第二次测评（含它自己的六维分），只有一次测评时为 null。
 *
 * 换算法时不要改这个类，新增一个 {@link AbilityProfileStrategy} 实现即可。
 */
@Component
public class LatestAssessmentProfileStrategy implements AbilityProfileStrategy {

    /** 趋势曲线的取数条数。 */
    public static final int TREND_LIMIT = 10;

    /** 配置 app.ability-profile.strategy 用这个名字选中本策略。 */
    public static final String NAME = "latest";

    @Override
    public String name() {
        return NAME;
    }

    @Override
    public AbilityProfile build(AbilityProfileContext context) {
        List<Assessment> history = context.history();
        if (history.isEmpty()) {
            return AbilityProfile.empty(context.classId());
        }

        Assessment newest = history.get(0);
        List<Assessment> recent = history.subList(0, Math.min(TREND_LIMIT, history.size()));

        // 趋势曲线按时间升序展示，而 history 是倒序的，这里翻过来
        List<AbilityProfile.Summary> trend = new ArrayList<>();
        for (int index = recent.size() - 1; index >= 0; index--) {
            trend.add(context.summaryOf(recent.get(index)));
        }

        return new AbilityProfile(
                context.classId(),
                true,
                context.summaryOf(newest),
                context.dimensionsOf(newest.getId()),
                context.pointsOf(newest.getId()),
                trend,
                previousOf(context, recent));
    }

    /** 倒数第二次测评；只有一次测评时返回 null（前端显示「完成第二次测评后生成对比」）。 */
    private AbilityProfile.Previous previousOf(AbilityProfileContext context, List<Assessment> recent) {
        if (recent.size() < 2) return null;
        Assessment earlier = recent.get(1);
        AbilityProfile.Summary summary = context.summaryOf(earlier);
        return new AbilityProfile.Previous(
                summary.assessmentId(),
                summary.averageScore(),
                summary.level(),
                summary.levelName(),
                summary.completedAt(),
                context.dimensionsOf(earlier.getId()));
    }
}
