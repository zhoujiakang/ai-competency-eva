package com.huiqiyikang.assessment.auth;

import cn.dev33.satoken.stp.StpUtil;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class AuthInterceptor implements HandlerInterceptor {
    @Override public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String uri = request.getRequestURI();
        // /api/auth/** 是登录注册本身；/api/client-logs 是前端错误上报——
        // 登录页出错时还没有令牌，所以这两个都必须放行。
        if (uri.startsWith("/api/auth/") || uri.startsWith("/api/client-logs")
                || "OPTIONS".equalsIgnoreCase(request.getMethod())) return true;
        StpUtil.checkLogin();
        return true;
    }
}
