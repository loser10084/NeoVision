package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.Min;
import lombok.Data;

@Data
public class PatientUpdateRequest {
    private String name;
    private String sex;
    @Min(value = 0, message = "age must be >= 0")
    private Integer age;
    private String stage;
    private String diagnosis;
}
