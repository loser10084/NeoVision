package com.yunchuan.smartimage_backend.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class FileUpload {
    private Long id;
    private Long patientId;
    private Long studyId;
    private String fileType;
    private String filePath;
    private Long sizeBytes;
    private Long uploaderId;
    private LocalDateTime createdAt;
}
