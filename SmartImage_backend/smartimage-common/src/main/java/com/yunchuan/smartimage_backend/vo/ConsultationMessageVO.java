package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class ConsultationMessageVO {
    private Long id;
    private Long consultationId;
    private Long senderId;
    private String senderName;
    private String messageType;
    private String textContent;
    private String ossPath;
    private String fileName;
    private Long fileSize;
    private String mimeType;
    private String createdAt;
}
