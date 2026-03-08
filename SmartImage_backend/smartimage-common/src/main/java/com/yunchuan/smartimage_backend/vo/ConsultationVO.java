package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class ConsultationVO {
    private Long id;
    private String title;
    private Long patientId;
    private Long creatorId;
    private String status;
    private String materialsOssPath;
    private String lastMessage;
    private String lastMessageAt;
    private String createdAt;
}
