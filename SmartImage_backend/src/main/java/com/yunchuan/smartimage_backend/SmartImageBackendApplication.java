package com.yunchuan.smartimage_backend;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.yunchuan.smartimage_backend.mapper")
public class SmartImageBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(SmartImageBackendApplication.class, args);
    }

}
