package com.yunchuan.smartimage_backend.security;

import jakarta.servlet.http.HttpServletRequest;

public class SecurityUtil {

    private SecurityUtil() {
    }

    public static Long currentUserId(HttpServletRequest request) {
        Object value = request.getAttribute("currentUserId");
        if (value instanceof Long) {
            return (Long) value;
        }
        if (value instanceof Integer) {
            return ((Integer) value).longValue();
        }
        return null;
    }
}
