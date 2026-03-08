package com.yunchuan.smartimage_backend.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ConsultationMessage {
    private Long id;
    private Long consultationId;
    private Long senderId;
    private String messageType;
    private String textContent;
    private String ossPath;
    private String fileName;
    private Long fileSize;
    private String mimeType;
    private LocalDateTime createdAt;
}
