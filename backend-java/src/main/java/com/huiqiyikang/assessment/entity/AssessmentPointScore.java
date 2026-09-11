package com.huiqiyikang.assessment.entity;
import com.baomidou.mybatisplus.annotation.*; import lombok.*; import java.time.Instant;
/** 考察点分：一次测评 × 一个考察点一行，技能树的数据源，由 Agent 收尾时幂等写入。 */
@TableName("assessment_point_scores") @Getter @Setter @NoArgsConstructor
public class AssessmentPointScore {
    @TableId(type=IdType.AUTO) Long id;
    Long assessmentId; Long classId; Long studentUserId;
    String dimension; String assessmentPoint; Double score; Integer questionCount;
    Instant createdAt = Instant.now();
}
