package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class FileVO {
    private Long id;
    private Long patientId;
    private Long studyId;
    private String fileType;
    private String filePath;
    private Long size;
}
