package com.smartagriculture.service;

import com.smartagriculture.model.ThresholdSetting;
import com.smartagriculture.model.User;
import com.smartagriculture.repository.ThresholdSettingRepository;
import com.smartagriculture.repository.UserRepository;
import com.smartagriculture.security.PasswordHasher;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 启动初始化：建表、初始化默认阈值、确保管理员账号可用。
 */
@Component
public class Initializer {

    private static final Logger log = LoggerFactory.getLogger(Initializer.class);

    private final JdbcTemplate jdbc;
    private final ThresholdSettingRepository thresholdSettingRepository;
    private final UserRepository userRepository;

    public Initializer(JdbcTemplate jdbc,
                       ThresholdSettingRepository thresholdSettingRepository,
                       UserRepository userRepository) {
        this.jdbc = jdbc;
        this.thresholdSettingRepository = thresholdSettingRepository;
        this.userRepository = userRepository;
    }

    @PostConstruct
    public void init() {
        try {
            boolean thresholdTableExisted = thresholdSettingRepository.tableExists();
            createTables();
            log.info("数据库表检查完成");
            if (!thresholdTableExisted) {
                initDefaultThresholds();
            }
            ensureAdminUser();
        } catch (Exception e) {
            log.error("数据库初始化失败，请检查数据库连接配置: {}", e.getMessage());
        }
    }

    private void createTables() {
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER NOT NULL AUTO_INCREMENT,
                    username VARCHAR(80) NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    email VARCHAR(120) NOT NULL,
                    is_active TINYINT(1),
                    created_at DATETIME,
                    role VARCHAR(20),
                    PRIMARY KEY (id),
                    UNIQUE KEY uk_users_username (username),
                    UNIQUE KEY uk_users_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER NOT NULL AUTO_INCREMENT,
                    timestamp DATETIME,
                    air_temperature FLOAT,
                    air_humidity FLOAT,
                    soil_temperature FLOAT,
                    soil_moisture FLOAT,
                    light_intensity FLOAT,
                    co2_concentration FLOAT,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS device_status (
                    id INTEGER NOT NULL AUTO_INCREMENT,
                    device_type VARCHAR(50) NOT NULL,
                    status INTEGER,
                    last_updated DATETIME,
                    description VARCHAR(100),
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER NOT NULL AUTO_INCREMENT,
                    user_id INTEGER,
                    operation_type VARCHAR(50) NOT NULL,
                    device_type VARCHAR(50),
                    operation_time DATETIME,
                    operation_result TINYINT(1),
                    description TEXT,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS threshold_settings (
                    id INTEGER NOT NULL AUTO_INCREMENT,
                    `name` VARCHAR(50) NOT NULL,
                    `type` VARCHAR(20) NOT NULL,
                    `operator` VARCHAR(5) NOT NULL,
                    `threshold` FLOAT NOT NULL,
                    `enabled` TINYINT(1),
                    `create_time` DATETIME,
                    `update_time` DATETIME,
                    `user_id` INTEGER,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """);
    }

    private void initDefaultThresholds() {
        List<ThresholdSetting> defaults = List.of(
                threshold("空气温度下限", "air_temperature", "<", 10),
                threshold("空气温度上限", "air_temperature", ">", 35),
                threshold("空气湿度下限", "air_humidity", "<", 30),
                threshold("空气湿度上限", "air_humidity", ">", 90),
                threshold("土壤温度下限", "soil_temperature", "<", 8),
                threshold("土壤温度上限", "soil_temperature", ">", 30),
                threshold("土壤湿度下限", "soil_moisture", "<", 15),
                threshold("土壤湿度上限", "soil_moisture", ">", 80),
                threshold("光照强度下限", "light_intensity", "<", 1000),
                threshold("光照强度上限", "light_intensity", ">", 50000),
                threshold("CO2浓度下限", "co2_concentration", "<", 300),
                threshold("CO2浓度上限", "co2_concentration", ">", 1200)
        );
        for (ThresholdSetting setting : defaults) {
            thresholdSettingRepository.insert(setting);
        }
        log.info("已初始化默认阈值设置，共 {} 条", defaults.size());
    }

    private ThresholdSetting threshold(String name, String type, String operator, double threshold) {
        ThresholdSetting setting = new ThresholdSetting();
        setting.name = name;
        setting.type = type;
        setting.operator = operator;
        setting.threshold = threshold;
        setting.enabled = true;
        setting.create_time = LocalDateTime.now();
        setting.update_time = LocalDateTime.now();
        setting.user_id = null;
        return setting;
    }

    private void ensureAdminUser() {
        User admin = userRepository.findByUsername("admin");
        if (admin == null) {
            User user = new User();
            user.username = "admin";
            user.passwordHash = PasswordHasher.hash("admin123");
            user.email = "admin@example.com";
            user.is_active = true;
            user.created_at = LocalDateTime.now();
            user.role = "admin";
            userRepository.insert(user);
            log.info("已创建管理员账号: admin");
            return;
        }
        if (admin.email == null || admin.email.isBlank()) {
            userRepository.updateEmail(admin.id, "admin@example.com");
            log.info("管理员账号邮箱已补全");
        }
        if (!PasswordHasher.isHashed(admin.passwordHash)) {
            userRepository.updatePasswordHash(admin.id, PasswordHasher.hash("admin123"));
            log.info("管理员账号密码哈希已更新");
        }
    }
}
