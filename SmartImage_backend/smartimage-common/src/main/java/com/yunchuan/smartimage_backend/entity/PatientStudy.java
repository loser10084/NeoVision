package com.yunchuan.smartimage_backend.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class PatientStudy {
    private Long id;
    private Long patientId;
    private String studyUid;
    private String modality;
    private String description;
    private String status;
    private LocalDateTime acquiredAt;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
