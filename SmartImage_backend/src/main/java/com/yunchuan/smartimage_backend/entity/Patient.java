package com.yunchuan.smartimage_backend.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class Patient {
    private Long id;
    private String patientNo;
    private String name;
    private String sex;
    private Integer age;
    private String stage;
    private String diagnosis;
    private Long attendingId;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
