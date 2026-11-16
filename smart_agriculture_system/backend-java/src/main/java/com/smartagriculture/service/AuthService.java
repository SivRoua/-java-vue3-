package com.smartagriculture.service;

import com.smartagriculture.model.User;
import com.smartagriculture.repository.UserRepository;
import com.smartagriculture.security.PasswordHasher;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * 认证服务：登录校验、注册与用户查询。
 */
@Service
public class AuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private final UserRepository userRepository;

    public AuthService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    /**
     * 校验用户名密码，成功返回用户信息 Map，失败返回 null。
     */
    public User authenticate(String username, String password) {
        User user = userRepository.findByUsername(username);
        if (user == null || !Boolean.TRUE.equals(user.is_active)) {
            log.warn("用户不存在: {}", username);
            return null;
        }
        if (!PasswordHasher.verify(user.passwordHash, password)) {
            log.warn("用户密码错误: {}", username);
            return null;
        }
        return user;
    }

    public User getUserById(String identity) {
        if (identity == null) {
            return null;
        }
        try {
            return userRepository.findById(Integer.parseInt(identity));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    public User getUserByUsername(String username) {
        return userRepository.findByUsername(username);
    }

    public boolean emailExists(String email) {
        return userRepository.existsByEmail(email);
    }

    public void createUser(String username, String password, String email,
                           String role, Boolean isActive) {
        User user = new User();
        user.username = username;
        user.passwordHash = PasswordHasher.hash(password);
        user.email = email;
        user.is_active = isActive != null ? isActive : Boolean.TRUE;
        user.created_at = LocalDateTime.now();
        user.role = role != null ? role : "user";
        userRepository.insert(user);
    }
}
