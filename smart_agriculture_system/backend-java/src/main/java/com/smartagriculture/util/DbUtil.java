package com.smartagriculture.util;

import java.sql.Timestamp;
import java.time.LocalDateTime;

public final class DbUtil {

    private DbUtil() {
    }

    public static LocalDateTime toLocalDateTime(Timestamp timestamp) {
        return timestamp != null ? timestamp.toLocalDateTime() : null;
    }

    /**
     * 写入/查询参数统一 +8h 补偿：connector 与云端 MySQL 的时区换算会使
     * 落库值 = 参数 - 8h，补偿后存储值、范围查询与回读显示均等于真实本地时间。
     */
    public static Timestamp toTimestamp(LocalDateTime value) {
        return value != null ? Timestamp.valueOf(value.plusHours(8)) : null;
    }

    public static Double nullableDouble(java.sql.ResultSet rs, String column) throws java.sql.SQLException {
        double value = rs.getDouble(column);
        return rs.wasNull() ? null : value;
    }

    public static Boolean nullableBoolean(java.sql.ResultSet rs, String column) throws java.sql.SQLException {
        boolean value = rs.getBoolean(column);
        return rs.wasNull() ? null : value;
    }

    public static Integer nullableInt(java.sql.ResultSet rs, String column) throws java.sql.SQLException {
        int value = rs.getInt(column);
        return rs.wasNull() ? null : value;
    }
}
