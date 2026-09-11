package com.huiqiyikang.assessment.entity;
import com.baomidou.mybatisplus.annotation.*; import lombok.*; import java.time.Instant;
@TableName("assessment_messages") @Getter @Setter @NoArgsConstructor
public class AssessmentMessage { @TableId(type=IdType.AUTO) Long id; Long assessmentId; Long assessmentQuestionId; String senderType; String content; Integer sequenceNo; Instant createdAt=Instant.now(); public AssessmentMessage(Long a,Long q,String sender,String content,Integer seq){assessmentId=a;assessmentQuestionId=q;senderType=sender;this.content=content;sequenceNo=seq;} }
