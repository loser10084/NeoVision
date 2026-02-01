package com.yunchuan.smartimage_backend.service;

import com.yunchuan.smartimage_backend.common.BusinessException;
import com.yunchuan.smartimage_backend.entity.AuditLog;
import com.yunchuan.smartimage_backend.entity.DoctorUser;
import com.yunchuan.smartimage_backend.mapper.AuditLogMapper;
import com.yunchuan.smartimage_backend.mapper.DoctorUserMapper;
import com.yunchuan.smartimage_backend.security.TokenManager;
import com.yunchuan.smartimage_backend.vo.AuthResponse;
import com.yunchuan.smartimage_backend.vo.UserVO;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class AuthService {

    private final DoctorUserMapper doctorUserMapper;
    private final AuditLogMapper auditLogMapper;
    private final TokenManager tokenManager;
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public AuthService(DoctorUserMapper doctorUserMapper, AuditLogMapper auditLogMapper, TokenManager tokenManager) {
        this.doctorUserMapper = doctorUserMapper;
        this.auditLogMapper = auditLogMapper;
        this.tokenManager = tokenManager;
    }

    public AuthResponse login(String username, String password) {
        if (!StringUtils.hasText(username) || !StringUtils.hasText(password)) {
            throw new BusinessException(400, "Invalid request");
        }
        DoctorUser user = doctorUserMapper.findByMobile(username);
        if (user == null || !passwordEncoder.matches(password, user.getPasswordHash())) {
            throw new BusinessException(401, "Invalid request");
        }
        String token = tokenManager.generateToken(user.getId());
        recordAudit(user.getId(), "login", "user login");
        AuthResponse response = new AuthResponse();
        response.setToken(token);
        response.setUser(toUserVO(user));
        return response;
    }

    public Long register(DoctorUser doctorUser) {
        if (doctorUserMapper.findByMobile(doctorUser.getMobile()) != null) {
            throw new BusinessException(409, "mobile already registered");
        }
        doctorUser.setPasswordHash(passwordEncoder.encode(doctorUser.getPasswordHash()));
        doctorUser.setStatus(1);
        doctorUserMapper.insert(doctorUser);
        recordAudit(doctorUser.getId(), "register", "user register");
        return doctorUser.getId();
    }

    private void recordAudit(Long userId, String action, String detail) {
        AuditLog log = new AuditLog();
        log.setUserId(userId);
        log.setAction(action);
        log.setDetail(detail);
        auditLogMapper.insert(log);
    }

    private UserVO toUserVO(DoctorUser user) {
        UserVO vo = new UserVO();
        vo.setId(user.getId());
        vo.setName(user.getName());
        vo.setHospital(user.getHospital());
        vo.setDept(user.getDept());
        vo.setMobile(user.getMobile());
        return vo;
    }
}
