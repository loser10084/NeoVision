package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class FileUploadRequest {
    @NotBlank(message = "fileType is required")
    private String fileType;
    private Long sizeBytes;
    private String filePath;
}
