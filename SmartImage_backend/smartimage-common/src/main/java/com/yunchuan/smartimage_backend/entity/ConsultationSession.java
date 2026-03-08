package com.yunchuan.smartimage_backend.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ConsultationSession {
    private Long id;
    private String title;
    private Long patientId;
    private Long creatorId;
    private String status;
    private String materialsOssPath;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
