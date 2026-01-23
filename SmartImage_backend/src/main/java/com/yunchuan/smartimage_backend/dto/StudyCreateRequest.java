package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class StudyCreateRequest {
    private String studyUid;
    @NotBlank(message = "模态不能为空")
    private String modality;
    private String desc;
    private String fileIds;
}
