package com.yunchuan.smartimage_backend.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class DoctorUser {
    private Long id;
    private String name;
    private String hospital;
    private String dept;
    private String mobile;
    private String passwordHash;
    private Integer status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
