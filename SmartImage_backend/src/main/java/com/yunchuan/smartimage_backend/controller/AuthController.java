package com.yunchuan.smartimage_backend.controller;

import com.yunchuan.smartimage_backend.common.ApiResponse;
import com.yunchuan.smartimage_backend.dto.LoginRequest;
import com.yunchuan.smartimage_backend.dto.RegisterRequest;
import com.yunchuan.smartimage_backend.entity.DoctorUser;
import com.yunchuan.smartimage_backend.service.AuthService;
import com.yunchuan.smartimage_backend.vo.AuthResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public ApiResponse<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        AuthResponse response = authService.login(request.getUsername(), request.getPassword());
        return ApiResponse.success(response);
    }

    @PostMapping("/register")
    public ApiResponse<Long> register(@Valid @RequestBody RegisterRequest request) {
        DoctorUser user = new DoctorUser();
        user.setName(request.getName());
        user.setHospital(request.getHospital());
        user.setDept(request.getDept());
        user.setMobile(request.getMobile());
        user.setPasswordHash(request.getPassword());
        Long id = authService.register(user);
        return ApiResponse.success(id);
    }
}
