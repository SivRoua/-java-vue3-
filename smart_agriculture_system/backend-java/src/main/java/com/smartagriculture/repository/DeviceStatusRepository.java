package com.smartagriculture.repository;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;

@Repository
public class DeviceStatusRepository {

    private final JdbcTemplate jdbc;

    public DeviceStatusRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public int upsert(String deviceType, int status) {
        int updated = jdbc.update(
                "UPDATE device_status SET status = ?, last_updated = ? WHERE device_type = ?",
                status, java.sql.Timestamp.valueOf(LocalDateTime.now()), deviceType);
        if (updated > 0) {
            return updated;
        }
        return jdbc.update(
                "INSERT INTO device_status (device_type, status, last_updated) VALUES (?, ?, ?)",
                deviceType, status, java.sql.Timestamp.valueOf(LocalDateTime.now()));
    }
}
