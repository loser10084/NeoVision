package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class PatientCreateRequest {
    @NotBlank(message = "姓名不能为空")
    private String name;
    @NotBlank(message = "性别不能为空")
    private String sex;
    @NotNull(message = "年龄不能为空")
    @Min(value = 0, message = "年龄必须为正数")
    private Integer age;
    private String stage;
    private String diagnosis;
    private String studyId;
}
