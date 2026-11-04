package com.smartagriculture.repository;

import com.smartagriculture.model.ThresholdSetting;
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
public class ThresholdSettingRepository {

    private static final RowMapper<ThresholdSetting> MAPPER = (rs, rowNum) -> {
        ThresholdSetting setting = new ThresholdSetting();
        setting.id = rs.getInt("id");
        setting.name = rs.getString("name");
        setting.type = rs.getString("type");
        setting.operator = rs.getString("operator");
        setting.threshold = DbUtil.nullableDouble(rs, "threshold");
        setting.enabled = DbUtil.nullableBoolean(rs, "enabled");
        setting.create_time = DbUtil.toLocalDateTime(rs.getTimestamp("create_time"));
        setting.update_time = DbUtil.toLocalDateTime(rs.getTimestamp("update_time"));
        setting.user_id = DbUtil.nullableInt(rs, "user_id");
        return setting;
    };

    private final JdbcTemplate jdbc;

    public ThresholdSettingRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<ThresholdSetting> findAll() {
        return jdbc.query("SELECT * FROM threshold_settings ORDER BY id", MAPPER);
    }

    public List<ThresholdSetting> findEnabled() {
        return jdbc.query("SELECT * FROM threshold_settings WHERE enabled = 1", MAPPER);
    }

    public ThresholdSetting findById(Integer id) {
        List<ThresholdSetting> list = jdbc.query(
                "SELECT * FROM threshold_settings WHERE id = ? LIMIT 1", MAPPER, id);
        return list.isEmpty() ? null : list.get(0);
    }

    public int insert(ThresholdSetting setting) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(connection -> {
            PreparedStatement ps = connection.prepareStatement(
                    "INSERT INTO threshold_settings (`name`, `type`, `operator`, `threshold`, `enabled`, "
                            + "`create_time`, `update_time`, `user_id`) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    Statement.RETURN_GENERATED_KEYS);
            ps.setString(1, setting.name);
            ps.setString(2, setting.type);
            ps.setString(3, setting.operator);
            ps.setObject(4, setting.threshold);
            ps.setObject(5, setting.enabled != null ? setting.enabled : Boolean.TRUE);
            ps.setTimestamp(6, DbUtil.toTimestamp(setting.create_time));
            ps.setTimestamp(7, DbUtil.toTimestamp(setting.update_time));
            ps.setObject(8, setting.user_id);
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        if (key != null) {
            setting.id = key.intValue();
        }
        return setting.id != null ? setting.id : 0;
    }

    public void update(ThresholdSetting setting) {
        jdbc.update("UPDATE threshold_settings SET `name` = ?, `type` = ?, `operator` = ?, `threshold` = ?, "
                        + "`enabled` = ?, `update_time` = ? WHERE id = ?",
                setting.name,
                setting.type,
                setting.operator,
                setting.threshold,
                setting.enabled,
                DbUtil.toTimestamp(setting.update_time),
                setting.id);
    }

    public void delete(Integer id) {
        jdbc.update("DELETE FROM threshold_settings WHERE id = ?", id);
    }

    public boolean tableExists() {
        List<String> tables = jdbc.queryForList("SHOW TABLES LIKE 'threshold_settings'", String.class);
        return !tables.isEmpty();
    }
}
