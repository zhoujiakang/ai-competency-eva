package com.huiqiyikang.assessment.controller;
import com.huiqiyikang.assessment.entity.*; import com.huiqiyikang.assessment.service.*;

import cn.dev33.satoken.stp.StpUtil;
import com.huiqiyikang.assessment.common.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController @RequestMapping("/api/assessment-tasks")
public class AssessmentTaskDetailController {
    private final TaskService tasks; private final ClassRoomService classes; private final ClassRoomService members; private final AccountService teachers;
    public AssessmentTaskDetailController(TaskService tasks,ClassRoomService classes,ClassRoomService members,AccountService teachers){this.tasks=tasks;this.classes=classes;this.members=members;this.teachers=teachers;}
    @GetMapping("/{id}") public ApiResponse<?> detail(@PathVariable Long id){AssessmentTask task=tasks.findById(id).orElseThrow(()->new BusinessException("测评任务不存在"));boolean teacher=teachers.existsByUserId(uid());boolean allowed=teacher&&task.getTeacherUserId().equals(uid())||members.findByClassIdAndStudentUserId(task.getClassId(),uid()).map(m->"active".equals(m.getStatus())).orElse(false);if(!allowed)throw new BusinessException("无权访问该测评任务");Map<String,Object> data=new LinkedHashMap<>();data.put("task",task);data.put("classroom",classes.findById(task.getClassId()).orElse(null));return ApiResponse.ok(data);}
    private Long uid(){return StpUtil.getLoginIdAsLong();}
}
