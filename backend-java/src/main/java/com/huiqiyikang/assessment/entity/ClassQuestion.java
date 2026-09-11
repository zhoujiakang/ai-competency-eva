package com.huiqiyikang.assessment.entity;
import com.baomidou.mybatisplus.annotation.*; import lombok.*; import java.time.Instant;
@TableName("class_questions") @Getter @Setter @NoArgsConstructor
public class ClassQuestion { @TableId(type=IdType.AUTO) Long id; Long classId; Long questionId; String status="active"; Instant addedAt=Instant.now(); Instant removedAt; public ClassQuestion(Long classId,Long questionId){this.classId=classId;this.questionId=questionId;} }
