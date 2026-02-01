package com.yunchuan.smartimage_backend.security;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.UUID;

@Component
public class TokenManager {

    private static final long EXPIRE_SECONDS = 3600L * 24;
    private static final String TOKEN_KEY_PREFIX = "auth:token:";
    private final StringRedisTemplate redisTemplate;

    public TokenManager(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public String generateToken(Long userId) {
        String token = UUID.randomUUID().toString().replace("-", "");
        redisTemplate.opsForValue().set(
                TOKEN_KEY_PREFIX + token,
                String.valueOf(userId),
                Duration.ofSeconds(EXPIRE_SECONDS)
        );
        return token;
    }

    public Long getUserId(String token) {
        if (token == null || token.isBlank()) {
            return null;
        }
        String value = redisTemplate.opsForValue().get(TOKEN_KEY_PREFIX + token);
        if (value == null) {
            return null;
        }
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException ex) {
            return null;
        }
    }
}
