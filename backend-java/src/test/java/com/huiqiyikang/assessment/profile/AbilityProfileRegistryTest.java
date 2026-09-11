package com.huiqiyikang.assessment.profile;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 画像策略注册表：新算法只要实现 AbilityProfileStrategy 就能被收进来，
 * 名字写错必须回落而不是把接口打挂。
 */
class AbilityProfileRegistryTest {

    /** 一个最小可用的假策略，用来验证"新增策略不用改注册表"。 */
    private static AbilityProfileStrategy fake(String name) {
        return new AbilityProfileStrategy() {
            @Override
            public String name() {
                return name;
            }

            @Override
            public AbilityProfile build(AbilityProfileContext context) {
                return AbilityProfile.empty(context.classId());
            }
        };
    }

    private static AbilityProfileStrategy latest() {
        return new LatestAssessmentProfileStrategy();
    }

    @Test
    void activeUsesTheConfiguredStrategy() {
        AbilityProfileStrategy weighted = fake("weighted-recent");
        AbilityProfileRegistry registry = new AbilityProfileRegistry(
                List.of(latest(), weighted), "weighted-recent");

        assertSame(weighted, registry.active());
        assertEquals(List.of("latest", "weighted-recent"), List.copyOf(registry.names()).stream()
                .sorted().toList());
    }

    @Test
    void unknownConfiguredNameFallsBackToLatest() {
        AbilityProfileStrategy latest = latest();
        AbilityProfileRegistry registry = new AbilityProfileRegistry(List.of(latest), "typo-name");

        assertSame(latest, registry.active());
    }

    @Test
    void strategyNameIsCaseInsensitiveAndTrimmed() {
        AbilityProfileStrategy latest = latest();
        AbilityProfileRegistry registry = new AbilityProfileRegistry(List.of(latest), "  LATEST ");

        assertSame(latest, registry.active());
    }

    @Test
    void byNamePicksAnExactStrategyAndFallsBackOtherwise() {
        AbilityProfileStrategy weighted = fake("weighted-recent");
        AbilityProfileStrategy latest = latest();
        AbilityProfileRegistry registry = new AbilityProfileRegistry(List.of(latest, weighted), "latest");

        assertSame(weighted, registry.byName("weighted-recent"));
        assertSame(latest, registry.byName("does-not-exist"));
        assertSame(latest, registry.byName(null));
    }

    @Test
    void duplicateStrategyNamesFailFast() {
        IllegalStateException error = assertThrows(IllegalStateException.class,
                () -> new AbilityProfileRegistry(List.of(fake("latest"), latest()), "latest"));

        assertTrue(error.getMessage().contains("latest"));
    }

    @Test
    void missingFallbackStrategyFailsFast() {
        assertThrows(IllegalStateException.class,
                () -> new AbilityProfileRegistry(List.of(fake("weighted-recent")), "weighted-recent"));
    }
}
