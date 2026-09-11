package com.huiqiyikang.assessment.controller;
import com.huiqiyikang.assessment.entity.*; import com.huiqiyikang.assessment.service.AccountService;

import cn.dev33.satoken.stp.StpUtil; import com.huiqiyikang.assessment.common.*;
import jakarta.validation.Valid; import jakarta.validation.constraints.*; import org.springframework.http.HttpStatus; import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder; import org.springframework.web.bind.annotation.*;
import java.util.Map; import java.util.HashMap;

@RestController @RequestMapping("/api/auth")
public class AuthController {
    private final AccountService accounts; private final BCryptPasswordEncoder encoder=new BCryptPasswordEncoder();
    public AuthController(AccountService accounts){this.accounts=accounts;}
    public record Register(@NotBlank String account,@NotBlank String password,@NotBlank String name,@NotBlank String nickname,String phone,String email,String organizationCode){}
    public record Login(@NotBlank String account,@NotBlank String password,@NotBlank String role){}
    @PostMapping("/register/student") public ApiResponse<?> student(@Valid @RequestBody Register r){return register(r,"student");}
    @PostMapping("/register/teacher") public ApiResponse<?> teacher(@Valid @RequestBody Register r){return register(r,"teacher");}
    private ApiResponse<?> register(Register r,String role){if(r.password().matches(".*[\\u3400-\\u9fff].*"))throw new BusinessException("密码不能包含中文");if(accounts.existsByUsername(r.account()))throw new BusinessException("账号已存在");User u=accounts.save(new User(r.account(),encoder.encode(r.password()),r.name(),r.nickname()));if(role.equals("student"))accounts.save(new Student(u));else accounts.save(new Teacher(u));return ApiResponse.ok(profile(u,role));}
    @PostMapping("/login") public ApiResponse<?> login(@Valid @RequestBody Login r){User u=accounts.findByUsername(r.account()).orElseThrow(()->new BusinessException("账号或密码错误",HttpStatus.UNAUTHORIZED));if(!encoder.matches(r.password(),u.getPasswordHash()))throw new BusinessException("账号或密码错误",HttpStatus.UNAUTHORIZED);boolean student=accounts.existsStudent(u.getId()),teacher=accounts.existsTeacher(u.getId());if(r.role().equalsIgnoreCase("student")&&!student)throw new BusinessException("当前账号暂无学生身份");if(r.role().equalsIgnoreCase("teacher")&&!teacher)throw new BusinessException("当前账号暂无教师身份");StpUtil.login(u.getId());return ApiResponse.ok(Map.of("tokenName",StpUtil.getTokenName(),"tokenValue",StpUtil.getTokenValue(),"user",profile(u,r.role().toLowerCase())));}
    @PostMapping("/logout") public ApiResponse<Void> logout(){StpUtil.logout();return ApiResponse.ok();}
    private Map<String,Object> profile(User u,String role){Map<String,Object> p=new HashMap<>();p.put("id",u.getId());p.put("account",u.getUsername());p.put("username",u.getUsername());p.put("name",u.getName());p.put("nickname",u.getNickname());p.put("role",role);return p;}
}
