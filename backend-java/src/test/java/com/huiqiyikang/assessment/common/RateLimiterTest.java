package com.huiqiyikang.assessment.common;

import org.junit.jupiter.api.Test;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 进程内限流：前端错误上报与加入班级都靠它挡住「无限重试」。
 */
class RateLimiterTest {

    @Test
    void allowsUpToTheLimitThenRejects() {
        RateLimiter limiter = new RateLimiter();

        for (int i = 0; i < 3; i++) {
            assertTrue(limiter.allow("k", 3, Duration.ofMinutes(1)), "第 " + (i + 1) + " 次应当放行");
        }
        assertFalse(limiter.allow("k", 3, Duration.ofMinutes(1)));
    }

    @Test
    void countsEachKeySeparately() {
        RateLimiter limiter = new RateLimiter();

        assertTrue(limiter.allow("a", 1, Duration.ofMinutes(1)));
        assertTrue(limiter.allow("b", 1, Duration.ofMinutes(1)));
        assertFalse(limiter.allow("a", 1, Duration.ofMinutes(1)));
    }

    @Test
    void windowExpiryLetsTheKeyThroughAgain() throws Exception {
        RateLimiter limiter = new RateLimiter();

        assertTrue(limiter.allow("k", 1, Duration.ofMillis(40)));
        assertFalse(limiter.allow("k", 1, Duration.ofMillis(40)));
        Thread.sleep(60);
        assertTrue(limiter.allow("k", 1, Duration.ofMillis(40)));
    }
}
