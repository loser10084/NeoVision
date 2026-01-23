package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ContourStatusUpdateRequest {
    @NotBlank(message = "状态不能为空")
    private String status;
}
