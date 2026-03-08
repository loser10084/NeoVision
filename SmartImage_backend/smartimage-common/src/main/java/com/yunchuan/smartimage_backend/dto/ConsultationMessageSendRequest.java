package com.yunchuan.smartimage_backend.dto;

import lombok.Data;

@Data
public class ConsultationMessageSendRequest {
    private String messageType;
    private String textContent;
    private String ossPath;
    private String fileName;
    private Long fileSize;
    private String mimeType;
}
