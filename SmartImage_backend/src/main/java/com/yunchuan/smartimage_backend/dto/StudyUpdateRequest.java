package com.yunchuan.smartimage_backend.dto;

import lombok.Data;

@Data
public class StudyUpdateRequest {
    private String studyUid;
    private String modality;
    private String desc;
    private String status;
}
