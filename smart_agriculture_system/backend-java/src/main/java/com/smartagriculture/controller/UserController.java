package com.smartagriculture.controller;

import com.smartagriculture.model.User;
import com.smartagriculture.repository.UserRepository;
import com.smartagriculture.security.PasswordHasher;
import com.smartagriculture.util.Maps;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class UserController {

    private static final Logger log = LoggerFactory.getLogger(UserController.class);

    private final UserRepository userRepository;

    public UserController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @GetMapping("/users")
    public ResponseEntity<Map<String, Object>> getUsers() {
        try {
            List<User> users = userRepository.findAll();
            List<Map<String, Object>> userList = new ArrayList<>();
            for (User user : users) {
                userList.add(user.toMap());
            }
            return ResponseEntity.ok(Maps.of("status", "success", "data", userList));
        } catch (Exception e) {
            log.error("获取用户列表失败: {}", e.getMessage());
            return ResponseEntity.status(500).body(Maps.of("status", "error", "message", e.getMessage()));
        }
    }

    @PostMapping("/users")
    public ResponseEntity<Map<String, Object>> createUser(@RequestBody(required = false) Map<String, Object> data) {
        try {
            if (data == null || data.isEmpty()) {
                return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "无效的请求数据"));
            }
            List<String> missing = new ArrayList<>();
            for (String field : List.of("username", "email", "password", "role")) {
                if (isBlank(data.get(field))) {
                    missing.add(field);
                }
            }
            if (!missing.isEmpty()) {
                return ResponseEntity.badRequest().body(Maps.of("status", "error",
                        "message", "缺少必要字段: " + String.join(", ", missing)));
            }
            String username = String.valueOf(data.get("username"));
            String email = String.valueOf(data.get("email"));
            String role = String.valueOf(data.get("role"));
            String password = String.valueOf(data.get("password"));

            if (userRepository.existsByUsername(username)) {
                return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "用户名已存在"));
            }
            if (userRepository.existsByEmail(email)) {
                return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "邮箱已存在"));
            }
            if (username.length() > 80) {
                return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "用户名长度不能超过80个字符"));
            }
            if (email.length() > 120) {
                return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "邮箱长度不能超过120个字符"));
            }
            if (role.length() > 20) {
                return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "角色长度不能超过20个字符"));
            }

            String passwordHash = PasswordHasher.hash(password);
            if (passwordHash.length() > 256) {
                return ResponseEntity.badRequest().body(Maps.of("status", "error",
                        "message", "密码哈希长度超出限制，请使用更短的密码"));
            }

            User user = new User();
            user.username = username;
            user.email = email;
            user.passwordHash = passwordHash;
            user.role = role;
            user.is_active = data.get("is_active") != null ? asBoolean(data.get("is_active"), true) : Boolean.TRUE;
            user.created_at = LocalDateTime.now();
            userRepository.insert(user);
            log.info("成功创建用户: {}", username);

            return ResponseEntity.status(201).body(Maps.of(
                    "status", "success",
                    "message", "用户创建成功",
                    "data", user.toMap()
            ));
        } catch (Exception e) {
            log.error("创建用户失败: {}", e.getMessage());
            return ResponseEntity.status(500).body(Maps.of("status", "error",
                    "message", "创建用户请求处理失败: " + e.getMessage()));
        }
    }

    @PutMapping("/users/{userId}")
    public ResponseEntity<Map<String, Object>> updateUser(@PathVariable Integer userId,
                                                          @RequestBody(required = false) Map<String, Object> data) {
        try {
            User user = userRepository.findById(userId);
            if (user == null) {
                return ResponseEntity.status(404).body(Maps.of("status", "error", "message", "用户不存在"));
            }
            if ("admin".equals(user.username)) {
                return ResponseEntity.status(403).body(Maps.of("status", "error", "message", "不能修改管理员用户"));
            }
            if (data == null) {
                data = Map.of();
            }

            if (data.containsKey("username") && !String.valueOf(data.get("username")).equals(user.username)) {
                String username = String.valueOf(data.get("username"));
                if (username.length() > 80) {
                    return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "用户名长度不能超过80个字符"));
                }
                if (userRepository.existsByUsername(username)) {
                    return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "用户名已存在"));
                }
                user.username = username;
            }

            if (data.containsKey("email") && !String.valueOf(data.get("email")).equals(user.email)) {
                String email = String.valueOf(data.get("email"));
                if (email.length() > 120) {
                    return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "邮箱长度不能超过120个字符"));
                }
                if (userRepository.existsByEmail(email)) {
                    return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "邮箱已存在"));
                }
                user.email = email;
            }

            if (data.containsKey("password") && data.get("password") != null) {
                user.passwordHash = PasswordHasher.hash(String.valueOf(data.get("password")));
            }

            if (data.containsKey("role") && data.get("role") != null) {
                String role = String.valueOf(data.get("role"));
                if (role.length() > 20) {
                    return ResponseEntity.badRequest().body(Maps.of("status", "error", "message", "角色长度不能超过20个字符"));
                }
                user.role = role;
            }

            if (data.containsKey("is_active") && data.get("is_active") != null) {
                user.is_active = asBoolean(data.get("is_active"), true);
            }

            userRepository.update(user);
            log.info("成功更新用户: {}", user.username);

            return ResponseEntity.ok(Maps.of(
                    "status", "success",
                    "message", "用户更新成功",
                    "data", user.toMap()
            ));
        } catch (Exception e) {
            log.error("更新用户失败: {}", e.getMessage());
            return ResponseEntity.status(500).body(Maps.of("status", "error", "message", e.getMessage()));
        }
    }

    @DeleteMapping("/users/{userId}")
    public ResponseEntity<Map<String, Object>> deleteUser(@PathVariable Integer userId, HttpServletRequest request) {
        try {
            User user = userRepository.findById(userId);
            if (user == null) {
                return ResponseEntity.status(404).body(Maps.of("status", "error", "message", "用户不存在"));
            }
            if ("admin".equals(user.username)) {
                return ResponseEntity.status(403).body(Maps.of("status", "error", "message", "不能删除管理员用户"));
            }
            User currentUser = (User) request.getAttribute("auth_user");
            if (currentUser != null && user.id.equals(currentUser.id)) {
                return ResponseEntity.status(403).body(Maps.of("status", "error", "message", "不能删除当前登录用户"));
            }

            userRepository.delete(userId);
            log.info("成功删除用户: {}", user.username);
            return ResponseEntity.ok(Maps.of("status", "success", "message", "用户删除成功"));
        } catch (Exception e) {
            log.error("删除用户失败: {}", e.getMessage());
            return ResponseEntity.status(500).body(Maps.of("status", "error", "message", e.getMessage()));
        }
    }

    private static boolean isBlank(Object value) {
        return value == null || String.valueOf(value).isBlank();
    }

    private static boolean asBoolean(Object value, boolean defaultValue) {
        if (value instanceof Boolean b) {
            return b;
        }
        if (value instanceof Number n) {
            return n.intValue() != 0;
        }
        if (value instanceof String s) {
            return "true".equalsIgnoreCase(s) || "1".equals(s);
        }
        return defaultValue;
    }
}
