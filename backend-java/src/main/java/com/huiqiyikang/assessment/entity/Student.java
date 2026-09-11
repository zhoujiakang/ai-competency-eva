package com.huiqiyikang.assessment.entity;
import com.baomidou.mybatisplus.annotation.*; import lombok.Getter; import lombok.NoArgsConstructor; import java.time.Instant;
@TableName("students") @Getter @NoArgsConstructor
public class Student { @TableId(type=IdType.AUTO) private Long id; private Long userId; private Instant createdAt=Instant.now(); public Student(User u){userId=u.getId();} }
