package com.yunchuan.smartimage_backend.dto;

import lombok.Data;

@Data
public class ContourUpsertRequest {
    private Long studyId;
    private String type;
    private String storagePath;
    private String confidenceMap;
    private String status;
    private Integer version;
}
