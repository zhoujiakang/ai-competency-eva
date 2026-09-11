package com.huiqiyikang.assessment.profile;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 画像策略注册表：把 Spring 扫到的所有 {@link AbilityProfileStrategy} 按名字收起来，
 * 按配置挑当前生效的那一个。
 *
 * 新增策略不需要改这里——只要实现接口并打上 @Component，就会被自动收集。
 *
 * 这里也是「策略名打错」的唯一兜底点：配置里写了不存在的名字时记一条 WARN，
 * 回落到默认的 latest，而不是让接口 500。
 */
@Component
public class AbilityProfileRegistry {

    private static final Logger logger = LoggerFactory.getLogger(AbilityProfileRegistry.class);

    /** 兜底策略名：即使配置写错，也要保证画像接口可用。 */
    public static final String FALLBACK = LatestAssessmentProfileStrategy.NAME;

    private final Map<String, AbilityProfileStrategy> strategies = new LinkedHashMap<>();
    private final String activeName;

    public AbilityProfileRegistry(
            List<AbilityProfileStrategy> discovered,
            @Value("${app.ability-profile.strategy:" + FALLBACK + "}") String activeName) {
        for (AbilityProfileStrategy strategy : discovered) {
            AbilityProfileStrategy previous = strategies.put(normalize(strategy.name()), strategy);
            if (previous != null) {
                throw new IllegalStateException("画像策略名重复：" + strategy.name());
            }
        }
        if (!strategies.containsKey(FALLBACK)) {
            throw new IllegalStateException("缺少兜底画像策略：" + FALLBACK);
        }
        String configured = normalize(activeName);
        if (!strategies.containsKey(configured)) {
            logger.warn("配置的画像策略 {} 不存在，回落到 {}；可用策略：{}",
                    activeName, FALLBACK, strategies.keySet());
            configured = FALLBACK;
        } else {
            logger.info("画像策略：{}（可用：{}）", configured, strategies.keySet());
        }
        this.activeName = configured;
    }

    /** 当前生效的策略（由 app.ability-profile.strategy 决定）。 */
    public AbilityProfileStrategy active() {
        return strategies.get(activeName);
    }

    /** 精确选用某个策略；名字不存在时回落到默认策略并记 WARN。 */
    public AbilityProfileStrategy byName(String name) {
        String key = normalize(name);
        AbilityProfileStrategy found = key == null ? null : strategies.get(key);
        if (found != null) return found;
        logger.warn("画像策略 {} 不存在，回落到 {}", name, FALLBACK);
        return strategies.get(FALLBACK);
    }

    /** 已注册的策略名，用于诊断与日志。 */
    public Set<String> names() {
        return Set.copyOf(strategies.keySet());
    }

    private static String normalize(String name) {
        return name == null || name.isBlank() ? null : name.trim().toLowerCase();
    }
}
