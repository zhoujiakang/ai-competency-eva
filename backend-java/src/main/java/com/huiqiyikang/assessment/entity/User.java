package com.huiqiyikang.assessment.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Getter; import lombok.NoArgsConstructor; import lombok.Setter;
import java.time.Instant;
@TableName("users")
@Getter @Setter @NoArgsConstructor
public class User {
    @TableId(type=IdType.AUTO) private Long id;
    private String username;
    private String passwordHash;
    private String name;
    private String nickname;
    private Instant createdAt=Instant.now();
    private Instant updatedAt=Instant.now();
    public User(String username,String passwordHash,String name,String nickname){this.username=username;this.passwordHash=passwordHash;this.name=name;this.nickname=nickname;}
}
