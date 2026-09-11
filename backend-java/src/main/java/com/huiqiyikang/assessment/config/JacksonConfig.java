package com.huiqiyikang.assessment.config;

import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.databind.ser.std.ToStringSerializer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Snowflake IDs are larger than JavaScript's safe integer range. Serialize
 * all Long values as JSON strings so the browser can round-trip them exactly.
 */
@Configuration
public class JacksonConfig {
    @Bean
    public SimpleModule longAsStringModule() {
        SimpleModule module = new SimpleModule("long-as-string");
        module.addSerializer(Long.class, ToStringSerializer.instance);
        module.addSerializer(Long.TYPE, ToStringSerializer.instance);
        return module;
    }
}
