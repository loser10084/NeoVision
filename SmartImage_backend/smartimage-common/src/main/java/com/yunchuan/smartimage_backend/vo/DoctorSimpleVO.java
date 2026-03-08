package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class DoctorSimpleVO {
    private Long id;
    private String name;
    private String hospital;
    private String dept;
    private String mobile;
    private boolean friend;
}
