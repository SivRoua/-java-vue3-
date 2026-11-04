package com.smartagriculture.model;

import com.smartagriculture.util.Maps;

import java.time.LocalDateTime;
import java.util.Map;

public class User {

    public Integer id;
    public String username;
    public String passwordHash;
    public String email;
    public Boolean is_active;
    public LocalDateTime created_at;
    public String role;

    public Map<String, Object> toMap() {
        return Maps.of(
                "id", id,
                "username", username,
                "email", email,
                "is_active", is_active != null ? is_active : Boolean.TRUE,
                "role", role != null ? role : "user",
                "created_at", created_at != null ? created_at.toString() : null
        );
    }

    /** 登录、刷新令牌返回的用户信息（不含创建时间） */
    public Map<String, Object> toAuthMap() {
        return Maps.of(
                "id", id,
                "username", username,
                "email", email != null ? email : "admin@example.com",
                "is_active", is_active != null ? is_active : Boolean.TRUE,
                "role", role
        );
    }
}
