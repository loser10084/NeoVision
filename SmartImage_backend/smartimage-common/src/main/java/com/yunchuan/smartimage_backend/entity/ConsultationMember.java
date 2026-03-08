package com.yunchuan.smartimage_backend.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ConsultationMember {
    private Long id;
    private Long consultationId;
    private Long doctorId;
    private String role;
    private LocalDateTime joinedAt;
}
