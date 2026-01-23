package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class FileUploadRequest {
    @NotBlank(message = "文件类型不能为空")
    private String fileType;
    private Long sizeBytes;
    private String filePath;
}
