package com.yunchuan.smartimage_backend.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class RegisterRequest {
    @NotBlank(message = "name is required")
    private String name;
    @NotBlank(message = "hospital is required")
    private String hospital;
    @NotBlank(message = "dept is required")
    private String dept;
    @NotBlank(message = "mobile is required")
    private String mobile;
    @NotBlank(message = "password is required")
    private String password;
}
