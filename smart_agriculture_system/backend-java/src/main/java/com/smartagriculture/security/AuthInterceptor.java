package com.smartagriculture.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartagriculture.model.User;
import com.smartagriculture.repository.UserRepository;
import com.smartagriculture.util.Maps;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.nio.charset.StandardCharsets;
import java.util.Map;

@Component
public class AuthInterceptor implements HandlerInterceptor {

    public static final String ATTR_USER = "auth_user";
    public static final String ATTR_IDENTITY = "auth_identity";
    public static final String ATTR_CLAIMS = "auth_claims";

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final JwtUtil jwtUtil;
    private final UserRepository userRepository;

    public AuthInterceptor(JwtUtil jwtUtil, UserRepository userRepository) {
        this.jwtUtil = jwtUtil;
        this.userRepository = userRepository;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
            throws Exception {
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }
        String path = request.getRequestURI();
        String method = request.getMethod().toUpperCase();
        boolean adminPath = path.startsWith("/api/users");
        boolean authRequired = adminPath
                || "/api/auth/profile".equals(path)
                || "/api/auth/refresh".equals(path)
                || (path.startsWith("/api/alerts/rules")
                && ("POST".equals(method) || "PUT".equals(method) || "DELETE".equals(method)));

        String header = request.getHeader("Authorization");
        JwtUtil.TokenPayload payload = null;
        JwtUtil.TokenException tokenError = null;
        if (header != null && header.startsWith("Bearer ")) {
            try {
                payload = jwtUtil.parse(header.substring(7).trim());
            } catch (JwtUtil.TokenException e) {
                tokenError = e;
            }
        }

        if (payload != null) {
            User user = payload.userId != null ? userRepository.findById(payload.userId) : null;
            if (user != null) {
                request.setAttribute(ATTR_USER, user);
            }
            request.setAttribute(ATTR_IDENTITY, payload.identity);
            request.setAttribute(ATTR_CLAIMS, payload.claims);
        }

        if (!authRequired) {
            return true;
        }

        if (header == null || header.isBlank() || tokenError != null) {
            if (tokenError != null) {
                return writeError(response, 401, tokenError.isExpired() ? "Token已过期" : "Token无效");
            }
            return writeError(response, 401, "缺少Token");
        }
        if (payload == null) {
            return writeError(response, 401, "Token无效");
        }

        if (adminPath) {
            if (payload.userId == null) {
                return writeError(response, 401, "Invalid token, missing user_id");
            }
            User user = userRepository.findById(payload.userId);
            if (user == null) {
                return writeError(response, 401, "User not found");
            }
            if (!"admin".equals(user.role)) {
                return writeError(response, 403, "Admin privileges required");
            }
            request.setAttribute(ATTR_USER, user);
        }
        return true;
    }

    private boolean writeError(HttpServletResponse response, int status, String message) throws Exception {
        response.setStatus(status);
        response.setContentType("application/json;charset=UTF-8");
        Map<String, Object> body = Maps.of("status", "error", "message", message);
        response.getOutputStream().write(MAPPER.writeValueAsBytes(body));
        response.getOutputStream().flush();
        return false;
    }
}
