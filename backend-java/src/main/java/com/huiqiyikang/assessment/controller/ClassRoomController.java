package com.huiqiyikang.assessment.controller;
import com.huiqiyikang.assessment.entity.*; import com.huiqiyikang.assessment.service.*;

import cn.dev33.satoken.stp.StpUtil; import com.huiqiyikang.assessment.common.*;
import jakarta.validation.Valid; import jakarta.validation.constraints.*; import org.springframework.dao.DataIntegrityViolationException; import org.springframework.http.HttpStatus; import org.springframework.transaction.annotation.Transactional; import org.springframework.web.bind.annotation.*; import java.security.SecureRandom; import java.time.Duration; import java.time.Instant; import java.util.*;

@RestController @RequestMapping("/api/classes")
public class ClassRoomController {
 private final ClassRoomService classes; private final ClassRoomService members; private final ClassRoomService codes; private final ClassRoomService classQuestions; private final QuestionService questions; private final AccountService students; private final AccountService teachers; private final SecureRandom random=new SecureRandom();
 private final AbilityService abilities;
 private final RateLimiter limiter;
 public ClassRoomController(ClassRoomService c,ClassRoomService m,ClassRoomService i,ClassRoomService q,QuestionService questions,AccountService s,AccountService t,AbilityService abilities,RateLimiter limiter){classes=c;members=m;codes=i;classQuestions=q;this.questions=questions;students=s;teachers=t;this.abilities=abilities;this.limiter=limiter;}
 public record Create(@NotBlank String name,String description){}
 @PostMapping public ApiResponse<?> create(@Valid @RequestBody Create r){Long uid=uid();if(!teachers.existsByUserId(uid))throw new BusinessException("只有教师可以创建班级");ClassRoom c=classes.save(new ClassRoom(uid,r.name(),r.description()));ClassInviteCode code=newInviteCode(c.getId());return ApiResponse.ok(Map.of("id",c.getId(),"name",c.getName(),"description",Optional.ofNullable(c.getDescription()).orElse(""),"inviteCode",code.getCode()));}
 @GetMapping("/managed") public ApiResponse<?> managed(){if(!teachers.existsByUserId(uid()))throw new BusinessException("当前账号不是教师");return ApiResponse.ok(classes.findByTeacherUserId(uid()));}
 @GetMapping("/joined") public ApiResponse<?> joined(){List<ClassMember> joinedList=members.findByStudentUserIdAndStatus(uid(),"active");if(joinedList.isEmpty())return ApiResponse.ok(List.of());Map<Long,ClassRoom> byId=new HashMap<>();for(ClassRoom c:classes.findAllById(joinedList.stream().map(ClassMember::getClassId).toList()))byId.put(c.getId(),c);return ApiResponse.ok(joinedList.stream().map(m->byId.get(m.getClassId())).filter(Objects::nonNull).toList());}
 /**
  * 学生能力数据：一次返回雷达图、技能树、趋势曲线、上一次对比需要的全部数据。
  * 所有查询都按 classId 隔离；调用者必须是该班级的 active 成员。
  */
 @GetMapping("/{id}/my-ability") public ApiResponse<?> myAbility(@PathVariable Long id){if(!members.findByClassIdAndStudentUserId(id,uid()).map(m->"active".equals(m.getStatus())).orElse(false))throw new BusinessException("不是该班级有效成员",HttpStatus.FORBIDDEN);return ApiResponse.ok(abilities.myAbility(id,uid()));}
 @GetMapping("/{id}") public ApiResponse<?> detail(@PathVariable Long id){ClassRoom c=classes.findById(id).orElseThrow(()->new BusinessException("班级不存在"));if(!c.getTeacherUserId().equals(uid())&&!members.findByClassIdAndStudentUserId(id,uid()).map(m->"active".equals(m.getStatus())).orElse(false))throw new BusinessException("无权访问该班级");Map<String,Object> data=new LinkedHashMap<>();data.put("classroom",c);data.put("memberCount",members.memberCount(id));data.put("questionCount",classQuestions.questionCount(id));data.put("inviteCode",codes.findFirstByClassIdAndStatus(id,"active").map(ClassInviteCode::getCode).orElse(null));return ApiResponse.ok(data);}
 @PostMapping("/join") @Transactional public ApiResponse<?> join(@RequestBody Map<String,String> body){Long uid=uid();
  // 邀请码是 8 位随机串，只要有耐心就能枚举；限流让枚举变得不划算。
  if(!limiter.allow("join:"+uid,10,Duration.ofMinutes(1)))throw new BusinessException("尝试过于频繁，请稍后再试",HttpStatus.TOO_MANY_REQUESTS);
  String input=body.getOrDefault("inviteCode","").trim().toUpperCase();ClassInviteCode code=codes.findByCodeAndStatus(input,"active").orElseThrow(()->new BusinessException("邀请码无效或已失效"));if(!students.existsByUserId(uid()))throw new BusinessException("当前账号不是学生");ClassMember m=members.findByClassIdAndStudentUserId(code.getClassId(),uid).orElse(null);if(m!=null&&"active".equals(m.getStatus()))throw new BusinessException("已加入该班级");if(m==null)members.save(new ClassMember(code.getClassId(),uid));else{m.setStatus("active");m.setLeftAt(null);m.setRemovedAt(null);members.save(m);}return ApiResponse.ok(classes.findById(code.getClassId()).orElseThrow());}
 @DeleteMapping("/{id}/leave") public ApiResponse<Void> leave(@PathVariable Long id){ClassMember m=members.findByClassIdAndStudentUserId(id,uid()).orElseThrow(()->new BusinessException("不是该班级成员"));m.setStatus("left");m.setLeftAt(Instant.now());members.save(m);return ApiResponse.ok();}
 @GetMapping("/{id}/members") public ApiResponse<?> memberList(@PathVariable Long id){owned(id);List<ClassMember> rows=members.findByClassIdAndStatus(id,"active");if(rows.isEmpty())return ApiResponse.ok(List.of());Map<Long,User> byId=new HashMap<>();for(User u:students.findAllById(rows.stream().map(ClassMember::getStudentUserId).toList()))byId.put(u.getId(),u);return ApiResponse.ok(rows.stream().map(m->memberView(m,byId.get(m.getStudentUserId()))).toList());}
 /** 成员列表要显示「这是谁」，但 class_members 里只有 user_id，名字得从 users 批量取。 */
 private Map<String,Object> memberView(ClassMember m,User u){Map<String,Object> d=new LinkedHashMap<>();d.put("id",m.getId());d.put("studentUserId",m.getStudentUserId());d.put("nickname",u==null?null:u.getNickname());d.put("name",u==null?null:u.getName());d.put("account",u==null?null:u.getUsername());d.put("joinedAt",m.getJoinedAt());return d;}
 @DeleteMapping("/{id}/members/{studentId}") public ApiResponse<Void> removeMember(@PathVariable Long id,@PathVariable Long studentId){owned(id);ClassMember m=members.findByClassIdAndStudentUserId(id,studentId).orElseThrow(()->new BusinessException("成员不存在"));m.setStatus("removed");m.setRemovedAt(Instant.now());members.save(m);return ApiResponse.ok();}
 @PostMapping("/{id}/invite-code") public ApiResponse<?> refresh(@PathVariable Long id){owned(id);codes.findFirstByClassIdAndStatus(id,"active").ifPresent(old->{old.setStatus("invalidated");old.setInvalidatedAt(Instant.now());codes.save(old);});return ApiResponse.ok(newInviteCode(id));}
 @GetMapping("/{id}/questions") public ApiResponse<?> classQuestions(@PathVariable Long id){owned(id);List<ClassQuestion> links=classQuestions.findQuestions(id,"active");if(links.isEmpty())return ApiResponse.ok(List.of());Map<Long,Question> byId=new HashMap<>();for(Question q:questions.findAllById(links.stream().map(ClassQuestion::getQuestionId).toList()))byId.put(q.getId(),q);return ApiResponse.ok(links.stream().map(x->byId.get(x.getQuestionId())).filter(Objects::nonNull).toList());}
 @PostMapping("/{id}/questions/{questionId}") public ApiResponse<?> addQuestion(@PathVariable Long id,@PathVariable Long questionId){owned(id);Question q=questions.findById(questionId).orElseThrow(()->new BusinessException("题目不存在"));if(!q.getOwnerUserId().equals(uid()))throw new BusinessException("只能添加自己拥有的题目");if(!"active".equals(q.getStatus()))throw new BusinessException("下线题目不能加入班级题库");ClassQuestion x=classQuestions.findByClassIdAndQuestionId(id,questionId).orElse(null);if(x==null) x=new ClassQuestion(id,questionId);x.setStatus("active");x.setRemovedAt(null);return ApiResponse.ok(classQuestions.save(x));}
 @DeleteMapping("/{id}/questions/{questionId}") public ApiResponse<Void> removeQuestion(@PathVariable Long id,@PathVariable Long questionId){owned(id);ClassQuestion x=classQuestions.findByClassIdAndQuestionId(id,questionId).orElseThrow(()->new BusinessException("班级题库中不存在该题目"));x.setStatus("removed");x.setRemovedAt(Instant.now());classQuestions.save(x);return ApiResponse.ok();}
 private Long uid(){return StpUtil.getLoginIdAsLong();} private void owned(Long id){ClassRoom c=classes.findById(id).orElseThrow(()->new BusinessException("班级不存在",HttpStatus.NOT_FOUND));if(!c.getTeacherUserId().equals(uid()))throw new BusinessException("无权操作该班级",HttpStatus.FORBIDDEN);}
 /** 邀请码可选字符：去掉容易看混的 I/O/0/1，读给学生的口头码不容易抄错。 */
 private static final String CODE_ALPHABET="ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
 private static final int CODE_LENGTH=8;
 private String newCode(){StringBuilder code=new StringBuilder(CODE_LENGTH);for(int i=0;i<CODE_LENGTH;i++)code.append(CODE_ALPHABET.charAt(random.nextInt(CODE_ALPHABET.length())));return code.toString();}
 /**
  * 生成并落库一个不重复的邀请码。
  *
  * 以前是「随机生成 → 直接 save」，撞上 code 的 UNIQUE 约束就抛 409 让用户重试；
  * 现在先查历史码（含已失效的）避开，再兜住并发下的唯一键冲突重试。
  */
 private ClassInviteCode newInviteCode(Long classId){for(int attempt=0;attempt<10;attempt++){String code=newCode();if(codes.findByCode(code).isPresent())continue;try{return codes.save(new ClassInviteCode(classId,code));}catch(DataIntegrityViolationException e){/* 并发撞码，重试 */}}throw new BusinessException("邀请码生成失败，请重试");}
}
