package com.huiqiyikang.assessment;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.mybatis.spring.annotation.MapperScan;

@SpringBootApplication
@MapperScan("com.huiqiyikang.assessment.mapper")
public class AssessmentApplication {
    public static void main(String[] args) { SpringApplication.run(AssessmentApplication.class, args); }
}
