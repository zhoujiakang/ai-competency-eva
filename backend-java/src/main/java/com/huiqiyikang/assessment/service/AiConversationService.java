package com.huiqiyikang.assessment.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.huiqiyikang.assessment.common.BusinessException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;

/**
 * Java 与 Python Agent 之间唯一的边界。
 *
 * 发题、判断该不该换题、写对话记忆、评分和结束全部归 Agent；Java 不解析模型输出，
 * 也不判断"还有没有下一题"。这里只做两件事：转发普通 JSON 请求、原样透传 SSE 流。
 */
@Service
public class AiConversationService {
    private final ObjectMapper mapper;
    private final String baseUrl;
    private final String token;
    private final HttpClient http;
    private final Duration readTimeout;

    public AiConversationService(ObjectMapper mapper, @Value("${app.agent.base-url}") String baseUrl,
            @Value("${app.agent.service-token:}") String token, @Value("${app.agent.connect-timeout-ms:3000}") long connect,
            @Value("${app.agent.read-timeout-ms:120000}") long read) {
        this.mapper = mapper;
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.token = token;
        this.readTimeout = Duration.ofMillis(read);
        // FastAPI/Uvicorn 本地是明文 HTTP，固定 HTTP/1.1，避免明文下的 HTTP/2 协商差异。
        this.http = HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofMillis(connect)).build();
    }

    public Object forwardGet(String path, Long userId) {
        return forward(path, "GET", null, userId);
    }

    public Object forwardPost(String path, Object body, Long userId) {
        return forward(path, "POST", body, userId);
    }

    /**
     * SSE 原样透传。
     *
     * Java 不看事件内容，收到 Agent 的响应后直接把字节流写给浏览器，
     * 所以 Agent 新增事件类型时这里不需要跟着改。
     */
    public void forwardStream(String path, Object body, Long userId, OutputStream out) {
        try {
            HttpRequest request = builder(path, userId)
                    .POST(HttpRequest.BodyPublishers.ofString(write(body), StandardCharsets.UTF_8)).build();
            HttpResponse<InputStream> response = http.send(request, HttpResponse.BodyHandlers.ofInputStream());
            if (response.statusCode() / 100 != 2)
                throw new BusinessException("Agent 调用失败：HTTP " + response.statusCode() + " " + readAll(response.body()));
            try (InputStream in = response.body()) {
                in.transferTo(out);
                out.flush();
            }
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            throw new BusinessException("Agent 转发失败：" + e.getMessage());
        }
    }

    private Object forward(String path, String method, Object body, Long userId) {
        try {
            HttpRequest.Builder builder = builder(path, userId);
            HttpRequest request = "GET".equals(method) ? builder.GET().build()
                    : builder.POST(HttpRequest.BodyPublishers.ofString(write(body), StandardCharsets.UTF_8)).build();
            HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() / 100 != 2)
                throw new BusinessException("Agent 调用失败：HTTP " + response.statusCode() + " " + response.body());
            return mapper.readValue(response.body(), Object.class);
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            throw new BusinessException("Agent 调用失败：" + e.getMessage());
        }
    }

    private String write(Object body) throws Exception {
        return mapper.writeValueAsString(body == null ? Map.of() : body);
    }

    private String readAll(InputStream in) {
        try (InputStream stream = in) {
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return "";
        }
    }

    private HttpRequest.Builder builder(String path, Long userId) {
        HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(baseUrl + path))
                .timeout(readTimeout)
                .header("Content-Type", "application/json")
                // 身份由 Java 校验后传给 Agent，Agent 不重复验登录态。
                .header("X-User-Id", String.valueOf(userId));
        if (!token.isBlank()) builder.header("Authorization", "Bearer " + token);
        return builder;
    }
}
