package com.huiqiyikang.assessment.entity;
import com.baomidou.mybatisplus.annotation.*; import lombok.Getter; import lombok.NoArgsConstructor; import java.time.Instant;
@TableName("teachers") @Getter @NoArgsConstructor
public class Teacher { @TableId(type=IdType.AUTO) private Long id; private Long userId; private Instant createdAt=Instant.now(); public Teacher(User u){userId=u.getId();} }
