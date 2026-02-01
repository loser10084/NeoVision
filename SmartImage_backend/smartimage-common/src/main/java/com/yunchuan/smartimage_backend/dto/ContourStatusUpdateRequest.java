package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ContourStatusUpdateRequest {
    @NotBlank(message = "status is required")
    private String status;
}
