package com.yunchuan.smartimage_backend.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ContourResult {
    private Long id;
    private Long patientId;
    private Long studyId;
    private String type;
    private Integer version;
    private String status;
    private String storagePath;
    private String confidenceMap;
    private Long createdBy;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
