package com.huiqiyikang.assessment.controller;

import com.huiqiyikang.assessment.common.ApiResponse;
import com.huiqiyikang.assessment.common.RateLimiter;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;

/**
 * 前端错误上报。
 *
 * 浏览器里的异常只显示给用户是不够的——现场出问题时，开发者除了用户一句
 * "打不开"什么都拿不到。这里把前端异常落到后端日志，运维可以直接看：
 *
 *     journalctl -u ai-assessment-backend | grep 前端错误
 *
 * 两个刻意的设计：
 *   · 免登录：登录页本身就可能出错，那时还没有令牌；
 *   · 只写日志、不做别的：不落库、不告警，成本几乎为零，也不需要新表。
 *
 * 防滥用有两层：前端自律（同类错误只报一次、每次会话上限 20 条）不可信，
 * 所以后端还有一层——按来源 IP 限流 + 长度截断 + 换行/控制字符清洗。
 * 清洗是必要的：免登录接口里的换行可以让攻击者往 journalctl 里伪造日志行。
 */
@RestController
@RequestMapping("/api/client-logs")
public class ClientLogController {

    private static final Logger logger = LoggerFactory.getLogger("client");
    private static final int MAX_REPORTS_PER_MINUTE = 60;

    private final RateLimiter limiter;

    public ClientLogController(RateLimiter limiter) {
        this.limiter = limiter;
    }

    public record Report(String kind, String message, String stack, String url, String userAgent) {
    }

    @PostMapping
    public ApiResponse<Void> report(@RequestBody(required = false) Report report, HttpServletRequest request) {
        if (report == null || report.message() == null || report.message().isBlank()) {
            return ApiResponse.ok();
        }
        // 超限直接静默丢弃：上报本身不该再给用户添麻烦，也不值得回 429 让前端重试。
        if (!limiter.allow("client-log:" + clientIp(request), MAX_REPORTS_PER_MINUTE, Duration.ofMinutes(1))) {
            return ApiResponse.ok();
        }
        logger.warn(
                "前端错误 kind={} url={} ua={} | {}{}",
                clip(report.kind(), 40),
                clip(report.url(), 300),
                clip(report.userAgent(), 200),
                clip(report.message(), 600),
                report.stack() == null || report.stack().isBlank()
                        ? ""
                        : "\n" + clip(report.stack(), 2000));
        return ApiResponse.ok();
    }

    private static String clip(String value, int max) {
        if (value == null) return "";
        // 去掉 CR/LF/Tab 与 ANSI 转义序列：前者能伪造日志行，后者能污染终端。
        String trimmed = value.replaceAll("\u001B\\[[0-9;]*[A-Za-z]", "")
                .replaceAll("[\\r\\n\\t]+", " ")
                .trim();
        return trimmed.length() <= max ? trimmed : trimmed.substring(0, max) + "…";
    }

    /** 取真实来源 IP：nginx 反代时远端地址都是网关，只能看 X-Forwarded-For 的第一段。 */
    private static String clientIp(HttpServletRequest request) {
        String forwarded = request.getHeader("X-Forwarded-For");
        if (forwarded != null && !forwarded.isBlank()) {
            return forwarded.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }
}
