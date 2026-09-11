package com.huiqiyikang.assessment.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import com.huiqiyikang.assessment.auth.AuthInterceptor;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    private final AuthInterceptor authInterceptor;
    public WebConfig(AuthInterceptor authInterceptor) { this.authInterceptor = authInterceptor; }
    @Value("${app.cors-origins}") private String origins;
    @Override public void addCorsMappings(CorsRegistry registry) { registry.addMapping("/api/**").allowedOrigins(origins.split(",")).allowedMethods("GET","POST","PUT","DELETE","OPTIONS").allowedHeaders("*").allowCredentials(true); }
    @Override public void addInterceptors(InterceptorRegistry registry) { registry.addInterceptor(authInterceptor).addPathPatterns("/api/**"); }
}
