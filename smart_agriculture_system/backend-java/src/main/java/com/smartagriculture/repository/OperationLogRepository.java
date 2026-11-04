package com.smartagriculture.repository;

import com.smartagriculture.model.OperationLog;
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
public class OperationLogRepository {

    private static final RowMapper<OperationLog> MAPPER = (rs, rowNum) -> {
        OperationLog log = new OperationLog();
        log.id = rs.getInt("id");
        log.user_id = DbUtil.nullableInt(rs, "user_id");
        log.operation_type = rs.getString("operation_type");
        log.device_type = rs.getString("device_type");
        log.operation_time = DbUtil.toLocalDateTime(rs.getTimestamp("operation_time"));
        log.operation_result = DbUtil.nullableBoolean(rs, "operation_result");
        log.description = rs.getString("description");
        return log;
    };

    private final JdbcTemplate jdbc;

    public OperationLogRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<OperationLog> findRecent(int limit) {
        return jdbc.query("SELECT * FROM operation_logs ORDER BY operation_time DESC LIMIT ?", MAPPER, limit);
    }

    public List<OperationLog> findAutoControl(int limit) {
        return jdbc.query("SELECT * FROM operation_logs WHERE operation_type = ? ORDER BY operation_time DESC LIMIT ?",
                MAPPER, "自动控制", limit);
    }

    public long countUnhandled() {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM operation_logs WHERE operation_result = 0", Long.class);
        return count != null ? count : 0;
    }

    public OperationLog findById(Integer id) {
        List<OperationLog> list = jdbc.query("SELECT * FROM operation_logs WHERE id = ? LIMIT 1", MAPPER, id);
        return list.isEmpty() ? null : list.get(0);
    }

    public void markHandled(Integer id) {
        jdbc.update("UPDATE operation_logs SET operation_result = 1 WHERE id = ?", id);
    }

    public int insert(OperationLog log) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(connection -> {
            PreparedStatement ps = connection.prepareStatement(
                    "INSERT INTO operation_logs (user_id, operation_type, device_type, operation_time, "
                            + "operation_result, description) VALUES (?, ?, ?, ?, ?, ?)",
                    Statement.RETURN_GENERATED_KEYS);
            ps.setObject(1, log.user_id);
            ps.setString(2, log.operation_type);
            ps.setObject(3, log.device_type);
            ps.setTimestamp(4, DbUtil.toTimestamp(log.operation_time));
            ps.setObject(5, log.operation_result);
            ps.setString(6, log.description);
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        if (key != null) {
            log.id = key.intValue();
        }
        return log.id != null ? log.id : 0;
    }
}
