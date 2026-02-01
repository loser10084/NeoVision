package com.yunchuan.smartimage_backend.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AuditLog {
    private Long id;
    private Long userId;
    private String action;
    private String detail;
    private LocalDateTime createdAt;
}
