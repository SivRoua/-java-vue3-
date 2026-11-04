package com.smartagriculture.repository;

import com.smartagriculture.model.User;
import com.smartagriculture.util.DbUtil;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.List;

@Repository
public class UserRepository {

    private static final RowMapper<User> MAPPER = (rs, rowNum) -> {
        User user = new User();
        user.id = rs.getInt("id");
        user.username = rs.getString("username");
        user.passwordHash = rs.getString("password_hash");
        user.email = rs.getString("email");
        user.is_active = DbUtil.nullableBoolean(rs, "is_active");
        user.created_at = DbUtil.toLocalDateTime(rs.getTimestamp("created_at"));
        user.role = rs.getString("role");
        return user;
    };

    private final JdbcTemplate jdbc;

    public UserRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public User findByUsername(String username) {
        List<User> users = jdbc.query("SELECT * FROM users WHERE username = ? LIMIT 1", MAPPER, username);
        return users.isEmpty() ? null : users.get(0);
    }

    public User findById(Integer id) {
        List<User> users = jdbc.query("SELECT * FROM users WHERE id = ? LIMIT 1", MAPPER, id);
        return users.isEmpty() ? null : users.get(0);
    }

    public List<User> findAll() {
        return jdbc.query("SELECT * FROM users ORDER BY id", MAPPER);
    }

    public boolean existsByUsername(String username) {
        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM users WHERE username = ?", Integer.class, username);
        return count != null && count > 0;
    }

    public boolean existsByEmail(String email) {
        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM users WHERE email = ?", Integer.class, email);
        return count != null && count > 0;
    }

    public int insert(User user) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(connection -> {
            PreparedStatement ps = connection.prepareStatement(
                    "INSERT INTO users (username, password_hash, email, is_active, created_at, role) "
                            + "VALUES (?, ?, ?, ?, ?, ?)",
                    Statement.RETURN_GENERATED_KEYS);
            ps.setString(1, user.username);
            ps.setString(2, user.passwordHash);
            ps.setString(3, user.email);
            ps.setObject(4, user.is_active != null ? user.is_active : Boolean.TRUE);
            ps.setTimestamp(5, DbUtil.toTimestamp(user.created_at));
            ps.setString(6, user.role != null ? user.role : "user");
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        if (key != null) {
            user.id = key.intValue();
        }
        return user.id != null ? user.id : 0;
    }

    public void update(User user) {
        jdbc.update("UPDATE users SET username = ?, password_hash = ?, email = ?, is_active = ?, role = ? WHERE id = ?",
                user.username,
                user.passwordHash,
                user.email,
                user.is_active != null ? user.is_active : Boolean.TRUE,
                user.role,
                user.id);
    }

    public void updatePasswordHash(Integer id, String passwordHash) {
        jdbc.update("UPDATE users SET password_hash = ? WHERE id = ?", passwordHash, id);
    }

    public void updateEmail(Integer id, String email) {
        jdbc.update("UPDATE users SET email = ? WHERE id = ?", email, id);
    }

    public void delete(Integer id) {
        jdbc.update("DELETE FROM users WHERE id = ?", id);
    }
}
