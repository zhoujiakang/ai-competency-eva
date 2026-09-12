package com.huiqiyikang.assessment.common;

import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

/**
 * 进程内的固定窗口限流。
 *
 * 两处需要它：前端错误上报（免登录，不设限就能刷爆日志）和加入班级
 * （邀请码可以被脚本枚举）。两者都是「多试几次也没关系，但不能无限试」的场景，
 * 用不着引入 Redis：后端目前单实例，窗口计数放内存即可。
 *
 * 只做尽力而为的兜底：条目数超过上限时清掉过期窗口，避免被大量不同 key 撑爆内存。
 * 重启即清零、多实例不共享，这些都不影响它要挡的东西。
 */
@Component
public class RateLimiter {
    private static final int MAX_KEYS = 20_000;

    private record Window(long startedAt, int count) {}

    private final ConcurrentMap<String, Window> windows = new ConcurrentHashMap<>();

    /** 同一 key 在 window 内最多放行 max 次；返回 false 表示这一请求应当被拒绝。 */
    public boolean allow(String key, int max, Duration window) {
        long now = System.currentTimeMillis();
        long span = window.toMillis();
        if (windows.size() > MAX_KEYS) {
            windows.entrySet().removeIf(entry -> now - entry.getValue().startedAt() >= span);
        }
        Window current = windows.compute(key, (ignored, previous) -> {
            if (previous == null || now - previous.startedAt() >= span) return new Window(now, 1);
            return new Window(previous.startedAt(), previous.count() + 1);
        });
        return current.count() <= max;
    }
}
