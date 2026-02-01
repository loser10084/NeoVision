package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class AuthResponse {
    private String token;
    private UserVO user;
}
