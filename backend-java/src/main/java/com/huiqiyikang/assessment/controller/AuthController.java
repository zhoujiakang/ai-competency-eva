package com.huiqiyikang.assessment.controller;
import com.huiqiyikang.assessment.entity.*; import com.huiqiyikang.assessment.service.AccountService;

import cn.dev33.satoken.stp.StpUtil; import com.huiqiyikang.assessment.common.*;
import jakarta.validation.Valid; import jakarta.validation.constraints.*; import org.springframework.http.HttpStatus; import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder; import org.springframework.web.bind.annotation.*;
import java.util.Map; import java.util.HashMap;

@RestController @RequestMapping("/api/auth")
public class AuthController {
    private final AccountService accounts; private final BCryptPasswordEncoder encoder=new BCryptPasswordEncoder();
    public AuthController(AccountService accounts){this.accounts=accounts;}
    public record Register(@NotBlank String account,@NotBlank String password,@NotBlank String name,@NotBlank String nickname,
            @Pattern(regexp="^$|^\\d{11}$",message="手机号应为 11 位数字") String phone,
            @Email(message="邮箱格式不正确") String email,String organizationCode){}
    public record Login(@NotBlank String account,@NotBlank String password,@NotBlank String role){}
    @PostMapping("/register/student") public ApiResponse<?> student(@Valid @RequestBody Register r){return register(r,"student");}
    @PostMapping("/register/teacher") public ApiResponse<?> teacher(@Valid @RequestBody Register r){return register(r,"teacher");}
    private ApiResponse<?> register(Register r,String role){if(r.password().matches(".*[\\u3400-\\u9fff].*"))throw new BusinessException("密码不能包含中文");if(accounts.existsByUsername(r.account()))throw new BusinessException("账号已存在");User u=new User(r.account(),encoder.encode(r.password()),r.name(),r.nickname());u.setPhone(blankToNull(r.phone()));u.setEmail(blankToNull(r.email()));u=accounts.save(u);if(role.equals("student"))accounts.save(new Student(u));else accounts.save(new Teacher(u));return ApiResponse.ok(profile(u,role));}
    @PostMapping("/login") public ApiResponse<?> login(@Valid @RequestBody Login r){
        // 角色必须是两个合法值之一：只写「if student && !student」「if teacher && !teacher」
        // 的话，传 role=admin 这类值两个判断都不命中，会被当成合法登录放过去。
        String role=r.role().trim().toLowerCase();if(!role.equals("student")&&!role.equals("teacher"))throw new BusinessException("角色不合法");
        User u=accounts.findByUsername(r.account()).orElseThrow(()->new BusinessException("账号或密码错误",HttpStatus.UNAUTHORIZED));if(!encoder.matches(r.password(),u.getPasswordHash()))throw new BusinessException("账号或密码错误",HttpStatus.UNAUTHORIZED);boolean student=accounts.existsStudent(u.getId()),teacher=accounts.existsTeacher(u.getId());if(role.equals("student")&&!student)throw new BusinessException("当前账号暂无学生身份");if(role.equals("teacher")&&!teacher)throw new BusinessException("当前账号暂无教师身份");StpUtil.login(u.getId());return ApiResponse.ok(Map.of("tokenName",StpUtil.getTokenName(),"tokenValue",StpUtil.getTokenValue(),"user",profile(u,role)));}
    @PostMapping("/logout") public ApiResponse<Void> logout(){StpUtil.logout();return ApiResponse.ok();}
    private Map<String,Object> profile(User u,String role){Map<String,Object> p=new HashMap<>();p.put("id",u.getId());p.put("account",u.getUsername());p.put("username",u.getUsername());p.put("name",u.getName());p.put("nickname",u.getNickname());p.put("phone",u.getPhone());p.put("email",u.getEmail());p.put("role",role);return p;}
    private static String blankToNull(String value){if(value==null)return null;String trimmed=value.trim();return trimmed.isEmpty()?null:trimmed;}
}
