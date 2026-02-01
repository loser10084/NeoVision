package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class PatientCreateRequest {
    @NotBlank(message = "name is required")
    private String name;
    @NotBlank(message = "sex is required")
    private String sex;
    @NotNull(message = "age is required")
    @Min(value = 0, message = "age must be >= 0")
    private Integer age;
    private String stage;
    private String diagnosis;
    private String studyId;
}
