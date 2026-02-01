package com.yunchuan.smartimage_backend;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication(scanBasePackages = "com.yunchuan.smartimage_backend")
@EnableDiscoveryClient
@MapperScan("com.yunchuan.smartimage_backend.mapper")
public class SmartImagePatientApplication {

    public static void main(String[] args) {
        SpringApplication.run(SmartImagePatientApplication.class, args);
    }
}
