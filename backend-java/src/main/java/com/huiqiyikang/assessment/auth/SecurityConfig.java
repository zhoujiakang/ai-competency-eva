package com.huiqiyikang.assessment.auth;
import org.springframework.context.annotation.*; import org.springframework.security.config.annotation.web.builders.HttpSecurity; import org.springframework.security.web.SecurityFilterChain; import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
@Configuration public class SecurityConfig { @Bean BCryptPasswordEncoder passwordEncoder(){return new BCryptPasswordEncoder();} @Bean SecurityFilterChain filterChain(HttpSecurity h)throws Exception{return h.csrf(c->c.disable()).authorizeHttpRequests(a->a.anyRequest().permitAll()).build();} }
