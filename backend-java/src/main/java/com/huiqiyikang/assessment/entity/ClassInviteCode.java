package com.huiqiyikang.assessment.entity;
import com.baomidou.mybatisplus.annotation.*; import lombok.*; import java.time.Instant;
@TableName("class_invite_codes") @Getter @Setter @NoArgsConstructor
public class ClassInviteCode { @TableId(type=IdType.AUTO) Long id; Long classId; String code; String status="active"; Instant createdAt=Instant.now(); Instant invalidatedAt; public ClassInviteCode(Long classId,String code){this.classId=classId;this.code=code;} }
