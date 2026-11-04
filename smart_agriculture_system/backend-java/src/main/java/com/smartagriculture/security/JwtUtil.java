package com.smartagriculture.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartagriculture.config.AppEnv;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 与 flask-jwt-extended 兼容的 HS256 JWT 签发与校验。
 */
@Component
public class JwtUtil {

    public static final long EXPIRES_SECONDS = 3600;

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private final byte[] secret;

    public JwtUtil() {
        this.secret = AppEnv.jwtSecret().getBytes(StandardCharsets.UTF_8);
    }

    public String createToken(String identity, Map<String, Object> extraClaims) {
        long now = Instant.now().getEpochSecond();
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("iat", now);
        payload.put("exp", now + EXPIRES_SECONDS);
        payload.put("sub", identity);
        if (extraClaims != null) {
            payload.putAll(extraClaims);
        }
        try {
            String header = base64Url(MAPPER.writeValueAsBytes(Map.of("typ", "JWT", "alg", "HS256")));
            String body = base64Url(MAPPER.writeValueAsBytes(payload));
            String signingInput = header + "." + body;
            return signingInput + "." + base64Url(sign(signingInput));
        } catch (Exception e) {
            throw new IllegalStateException("生成Token失败", e);
        }
    }

    public TokenPayload parse(String token) throws TokenException {
        if (token == null || token.isBlank()) {
            throw new TokenException(false);
        }
        String[] parts = token.split("\\.");
        if (parts.length != 3) {
            throw new TokenException(false);
        }
        String signingInput = parts[0] + "." + parts[1];
        byte[] expected;
        try {
            expected = sign(signingInput);
        } catch (Exception e) {
            throw new TokenException(false);
        }
        byte[] actual = decodeBase64Url(parts[2]);
        if (actual.length == 0 || !MessageDigest.isEqual(expected, actual)) {
            throw new TokenException(false);
        }
        Map<String, Object> claims;
        try {
            claims = MAPPER.readValue(decodeBase64Url(parts[1]), new com.fasterxml.jackson.core.type.TypeReference<>() {
            });
        } catch (Exception e) {
            throw new TokenException(false);
        }
        Object exp = claims.get("exp");
        if (exp instanceof Number) {
            if (((Number) exp).longValue() < Instant.now().getEpochSecond()) {
                throw new TokenException(true);
            }
        } else {
            throw new TokenException(false);
        }

        TokenPayload payload = new TokenPayload();
        payload.claims = claims;
        payload.identity = claims.get("sub") != null ? String.valueOf(claims.get("sub")) : null;
        payload.userId = parseInteger(claims.get("user_id"));
        payload.username = claims.get("username") != null ? String.valueOf(claims.get("username")) : null;
        payload.role = claims.get("role") != null ? String.valueOf(claims.get("role")) : null;
        if (payload.userId == null && payload.identity != null) {
            payload.userId = parseInteger(payload.identity);
        }
        return payload;
    }

    private static Integer parseInteger(Object value) {
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        if (value instanceof String s) {
            try {
                return Integer.parseInt(s);
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }

    private byte[] sign(String signingInput) throws Exception {
        javax.crypto.Mac mac = javax.crypto.Mac.getInstance("HmacSHA256");
        mac.init(new javax.crypto.spec.SecretKeySpec(secret, "HmacSHA256"));
        return mac.doFinal(signingInput.getBytes(StandardCharsets.UTF_8));
    }

    private static String base64Url(byte[] value) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(value);
    }

    private static byte[] decodeBase64Url(String value) {
        try {
            return Base64.getUrlDecoder().decode(value);
        } catch (Exception e) {
            return new byte[0];
        }
    }

    public static class TokenPayload {
        public String identity;
        public Integer userId;
        public String username;
        public String role;
        public Map<String, Object> claims;
    }

    public static class TokenException extends RuntimeException {
        private final boolean expired;

        public TokenException(boolean expired) {
            super(expired ? "Token已过期" : "Token无效");
            this.expired = expired;
        }

        public boolean isExpired() {
            return expired;
        }
    }
}
