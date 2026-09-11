package com.huiqiyikang.assessment.profile;

/**
 * 画像算法策略：给定一个学生在一个班级下的材料，算出他的能力画像。
 *
 * 这是画像模块唯一的扩展点。想换算法（最近 N 次加权、时间衰减、取最高分、
 * 按考察点覆盖率加权……）只需要：
 *
 *   1. 新建一个类实现本接口，返回自己的 {@link #name()}；
 *   2. 打上 @Component 让 Spring 扫到（{@link AbilityProfileRegistry} 会自动收集）；
 *   3. 把 app.ability-profile.strategy 配成这个名字，或者调用
 *      registry.byName("你的名字") 精确选用。
 *
 * 不需要改控制器、接口形状或任何调用方。算法只在读取时计算，所以换算法之后
 * 历史测评会立刻按新口径重新呈现，不用重跑测评或做数据迁移。
 */
public interface AbilityProfileStrategy {

    /** 策略名，用于配置与精确选用；约定全小写、短横线分词，例如 latest、weighted-recent。 */
    String name();

    /** 构建画像。没有测评时返回 {@link AbilityProfile#empty(Long)}。 */
    AbilityProfile build(AbilityProfileContext context);
}
