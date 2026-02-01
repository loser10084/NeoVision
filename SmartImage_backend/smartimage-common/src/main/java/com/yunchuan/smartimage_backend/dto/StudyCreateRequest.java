package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class StudyCreateRequest {
    private String studyUid;
    @NotBlank(message = "modality is required")
    private String modality;
    private String desc;
    private String fileIds;
}
