package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class StudyVO {
    private Long id;
    private String studyUid;
    private String modality;
    private String desc;
    private String status;
    private String time;
}
