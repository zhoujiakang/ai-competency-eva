package com.huiqiyikang.assessment.controller;
import com.huiqiyikang.assessment.entity.User; import com.huiqiyikang.assessment.service.AccountService;
import cn.dev33.satoken.stp.StpUtil;
import com.huiqiyikang.assessment.common.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.*;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
@RestController @RequestMapping("/api/users")
public class UserController {
 private final AccountService users; private final BCryptPasswordEncoder encoder;
 public UserController(AccountService u,BCryptPasswordEncoder e){users=u;encoder=e;}
 public record Profile(String name,String nickname,@Pattern(regexp="^$|^\\d{11}$",message="手机号应为 11 位数字") String phone,@Email(message="邮箱格式不正确") String email){}
 public record Password(@NotBlank String oldPassword,@NotBlank String newPassword){}
 @GetMapping("/me") public ApiResponse<?> me(){return ApiResponse.ok(profile(current()));}
 @PutMapping("/me") public ApiResponse<?> update(@Valid @RequestBody Profile p){User u=current();if(p.name()!=null&&!p.name().isBlank())u.setName(p.name());if(p.nickname()!=null&&!p.nickname().isBlank())u.setNickname(p.nickname());if(p.phone()!=null)u.setPhone(blankToNull(p.phone()));if(p.email()!=null)u.setEmail(blankToNull(p.email()));u.setUpdatedAt(Instant.now());return ApiResponse.ok(profile(users.save(u)));}
 @PutMapping("/password") public ApiResponse<?> password(@Valid @RequestBody Password p){User u=current();if(!encoder.matches(p.oldPassword(),u.getPasswordHash()))throw new BusinessException("旧密码错误");if(p.newPassword().matches(".*[\\u3400-\\u9fff].*"))throw new BusinessException("密码不能包含中文");u.setPasswordHash(encoder.encode(p.newPassword()));u.setUpdatedAt(Instant.now());users.save(u);return ApiResponse.ok();}
 private User current(){return users.findById(StpUtil.getLoginIdAsLong()).orElseThrow(()->new BusinessException("用户不存在"));}
 private Map<String,Object> profile(User u){Map<String,Object> p=new HashMap<>();p.put("id",u.getId());p.put("account",u.getUsername());p.put("name",u.getName());p.put("nickname",u.getNickname());p.put("phone",u.getPhone());p.put("email",u.getEmail());p.put("registeredAt",u.getCreatedAt());return p;}
 private static String blankToNull(String value){String trimmed=value.trim();return trimmed.isEmpty()?null:trimmed;}
}
