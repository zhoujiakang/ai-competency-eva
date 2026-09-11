package com.huiqiyikang.assessment.entity;
import com.baomidou.mybatisplus.annotation.*; import lombok.*; import java.time.Instant;
/**
 * 个人班级画像：每个「学生 × 班级」一行，只保留该班级下最新一次测评的分数与等级。
 *
 * 写入方是 Agent 在测评收尾时 upsert；教师端后续做班级分析、学生档案时直接读这张表。
 * 维度分与考察点分不在这里冗余，按 assessmentId 从各自的分数表读取。
 */
@TableName("student_class_profiles") @Getter @Setter @NoArgsConstructor
public class StudentClassProfile {
    @TableId(type = IdType.AUTO) Long id;
    Long classId; Long studentUserId; Long assessmentId;
    Double averageScore; String abilityLevel; Instant completedAt;
    Instant updatedAt = Instant.now();
}
