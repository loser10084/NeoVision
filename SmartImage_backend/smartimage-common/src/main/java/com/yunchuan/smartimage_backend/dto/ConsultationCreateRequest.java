package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.util.List;

@Data
public class ConsultationCreateRequest {
    @NotBlank(message = "title is required")
    private String title;
    private Long patientId;
    private List<Long> memberIds;
    private String materialsOssPath;
}
