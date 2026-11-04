package com.smartagriculture.controller;

import com.smartagriculture.model.User;
import com.smartagriculture.security.JwtUtil;
import com.smartagriculture.service.AuthService;
import com.smartagriculture.util.Maps;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private static final Logger log = LoggerFactory.getLogger(AuthController.class);

    private final AuthService authService;
    private final JwtUtil jwtUtil;

    public AuthController(AuthService authService, JwtUtil jwtUtil) {
        this.authService = authService;
        this.jwtUtil = jwtUtil;
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody(required = false) Map<String, Object> data) {
        try {
            if (data == null || data.isEmpty()) {
                return ResponseEntity.badRequest().body(Maps.of("error", "无效的请求数据"));
            }
            String username = asString(data.get("username"));
            String password = asString(data.get("password"));
            if (username == null || password == null || username.isEmpty() || password.isEmpty()) {
                return ResponseEntity.badRequest().body(Maps.of("error", "用户名和密码不能为空"));
            }

            User user = authService.authenticate(username, password);
            if (user == null) {
                return ResponseEntity.status(401).body(Maps.of("error", "用户名或密码错误"));
            }

            Map<String, Object> claims = new LinkedHashMap<>();
            claims.put("user_id", user.id);
            claims.put("username", user.username);
            claims.put("role", user.role != null ? user.role : "user");
            String accessToken = jwtUtil.createToken(String.valueOf(user.id), claims);
            log.info("用户登录成功: {}", username);

            return ResponseEntity.ok(Maps.of(
                    "access_token", accessToken,
                    "user", user.toMap()
            ));
        } catch (Exception e) {
            log.error("登录过程中发生错误: {}", e.getMessage());
            return ResponseEntity.status(500).body(Maps.of("error", "登录过程中发生错误"));
        }
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> register(@RequestBody(required = false) Map<String, Object> data) {
        try {
            if (data == null || data.isEmpty()) {
                return ResponseEntity.badRequest().body(Maps.of("error", "无效的请求数据"));
            }
            String username = asString(data.get("username"));
            String password = asString(data.get("password"));
            String email = asString(data.get("email"));
            String adminUsername = asString(data.get("admin_username"));
            String adminPassword = asString(data.get("admin_password"));
            if (username == null || password == null || email == null
                    || adminUsername == null || adminPassword == null) {
                return ResponseEntity.badRequest().body(Maps.of("error", "所有字段都不能为空"));
            }

            User admin = authService.authenticate(adminUsername, adminPassword);
            if (admin == null || !"admin".equals(admin.role)) {
                return ResponseEntity.status(401).body(Maps.of("error", "管理员验证失败，无法注册新用户"));
            }
            if (authService.getUserByUsername(username) != null) {
                return ResponseEntity.badRequest().body(Maps.of("error", "用户名已存在"));
            }
            if (authService.emailExists(email)) {
                return ResponseEntity.badRequest().body(Maps.of("error", "邮箱已存在"));
            }

            authService.createUser(username, password, email, "user", Boolean.TRUE);
            return ResponseEntity.ok(Maps.of(
                    "status", "success",
                    "message", "用户注册成功",
                    "username", username
            ));
        } catch (Exception e) {
            log.error("注册过程中发生错误: {}", e.getMessage());
            return ResponseEntity.status(500).body(Maps.of("error", "注册过程中发生错误"));
        }
    }

    @GetMapping("/profile")
    public ResponseEntity<Map<String, Object>> profile(HttpServletRequest request) {
        try {
            String identity = (String) request.getAttribute("auth_identity");
            User user = authService.getUserById(identity);
            if (user == null) {
                return ResponseEntity.status(404).body(Maps.of("error", "用户不存在"));
            }
            return ResponseEntity.ok(user.toMap());
        } catch (Exception e) {
            log.error("获取用户信息失败: {}", e.getMessage());
            return ResponseEntity.status(500).body(Maps.of("error", "获取用户信息失败"));
        }
    }

    @PostMapping("/refresh")
    public ResponseEntity<Map<String, Object>> refresh(HttpServletRequest request) {
        try {
            String identity = (String) request.getAttribute("auth_identity");
            User user = authService.getUserById(identity);
            if (user == null) {
                return ResponseEntity.status(404).body(Maps.of("error", "用户不存在"));
            }
            String accessToken = jwtUtil.createToken(identity, Map.of());
            log.info("用户令牌刷新成功: {}", user.username);
            return ResponseEntity.ok(Maps.of(
                    "access_token", accessToken,
                    "user", user.toMap()
            ));
        } catch (Exception e) {
            log.error("刷新令牌失败: {}", e.getMessage());
            return ResponseEntity.status(500).body(Maps.of("error", "刷新令牌失败"));
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<Map<String, Object>> logout() {
        return ResponseEntity.ok(Maps.of("status", "success", "message", "登出成功"));
    }

    private static String asString(Object value) {
        return value == null ? null : String.valueOf(value);
    }
}
