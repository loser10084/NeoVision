package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class ConsultationMemberVO {
    private Long doctorId;
    private String name;
    private String hospital;
    private String dept;
    private String mobile;
    private String role;
    private String joinedAt;
}
