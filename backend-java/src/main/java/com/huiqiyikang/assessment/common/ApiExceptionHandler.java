package com.huiqiyikang.assessment.common;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.bind.MethodArgumentNotValidException;
import cn.dev33.satoken.exception.NotLoginException;
import org.springframework.dao.DataIntegrityViolationException;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(BusinessException.class)
    ResponseEntity<ApiResponse<Void>> business(BusinessException e) { return ResponseEntity.status(e.status()).body(new ApiResponse<>(e.status().value(), e.getMessage(), null)); }
    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ApiResponse<Void>> validation(MethodArgumentNotValidException e) { return ResponseEntity.badRequest().body(new ApiResponse<>(400, e.getBindingResult().getFieldError().getDefaultMessage(), null)); }
    @ExceptionHandler(NotLoginException.class)
    ResponseEntity<ApiResponse<Void>> notLogin(NotLoginException e) { return ResponseEntity.status(401).body(new ApiResponse<>(401, "请先登录", null)); }
    @ExceptionHandler(DataIntegrityViolationException.class)
    ResponseEntity<ApiResponse<Void>> conflict(DataIntegrityViolationException e) { return ResponseEntity.status(409).body(new ApiResponse<>(409, "请求与已有数据冲突，请刷新后重试", null)); }
}
