package com.huiqiyikang.assessment.controller;

import com.huiqiyikang.assessment.common.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.*;

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
 * 防滥用靠前端自律（同类错误只报一次、每次会话上限 20 条）+ 这里的长度截断。
 */
@RestController
@RequestMapping("/api/client-logs")
public class ClientLogController {

    private static final Logger logger = LoggerFactory.getLogger("client");

    public record Report(String kind, String message, String stack, String url, String userAgent) {
    }

    @PostMapping
    public ApiResponse<Void> report(@RequestBody(required = false) Report report) {
        if (report == null || report.message() == null || report.message().isBlank()) {
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
        String trimmed = value.trim();
        return trimmed.length() <= max ? trimmed : trimmed.substring(0, max) + "…";
    }
}
