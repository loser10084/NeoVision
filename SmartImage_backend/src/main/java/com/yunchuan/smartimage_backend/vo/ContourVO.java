package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class ContourVO {
    private Long id;
    private Long studyId;
    private String type;
    private String status;
    private Integer version;
    private String storagePath;
    private String confidenceMap;
}
