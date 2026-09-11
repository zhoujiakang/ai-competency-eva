package com.huiqiyikang.assessment.entity;
import com.baomidou.mybatisplus.annotation.*; import lombok.*; import java.time.Instant;
/** 维度分：一次测评 × 一个维度一行，雷达图的数据源，由 Agent 收尾时幂等写入。 */
@TableName("assessment_dimension_scores") @Getter @Setter @NoArgsConstructor
public class AssessmentDimensionScore {
    @TableId(type=IdType.AUTO) Long id;
    Long assessmentId; Long classId; Long studentUserId;
    String dimension; Double score; Integer questionCount;
    Instant createdAt = Instant.now();
}
