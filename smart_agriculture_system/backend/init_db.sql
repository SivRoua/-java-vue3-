-- 创建数据库
CREATE DATABASE IF NOT EXISTS smart_agriculture DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE smart_agriculture;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(80) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(256) NOT NULL COMMENT '密码哈希',
    email VARCHAR(120) NOT NULL UNIQUE COMMENT '邮箱',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    role VARCHAR(20) DEFAULT 'user' COMMENT '用户角色'
) COMMENT '用户信息表';

-- 传感器数据表
CREATE TABLE IF NOT EXISTS sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '数据ID',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
    air_temperature FLOAT COMMENT '空气温度(°C)',
    air_humidity FLOAT COMMENT '空气湿度(%)',
    soil_temperature FLOAT COMMENT '土壤温度(°C)',
    soil_moisture FLOAT COMMENT '土壤湿度(%)',
    light_intensity FLOAT COMMENT '光照强度(lux)',
    co2_concentration FLOAT COMMENT 'CO2浓度(ppm)'
) COMMENT '传感器数据表';

-- 设备状态表
CREATE TABLE IF NOT EXISTS device_status (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '状态ID',
    device_type VARCHAR(50) NOT NULL COMMENT '设备类型',
    status BOOLEAN DEFAULT FALSE COMMENT '设备状态',
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    description VARCHAR(100) COMMENT '设备描述'
) COMMENT '设备状态表';

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    user_id INT COMMENT '操作用户ID',
    operation_type VARCHAR(50) NOT NULL COMMENT '操作类型',
    device_type VARCHAR(50) COMMENT '设备类型',
    operation_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    operation_result BOOLEAN COMMENT '操作结果',
    description TEXT COMMENT '操作描述'
) COMMENT '操作日志表';

-- 创建阈值设置表
CREATE TABLE IF NOT EXISTS threshold_settings (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '规则ID',
    name VARCHAR(50) NOT NULL COMMENT '规则名称',
    type VARCHAR(20) NOT NULL COMMENT '监测类型',
    operator VARCHAR(5) NOT NULL COMMENT '触发条件操作符',
    threshold FLOAT NOT NULL COMMENT '阈值',
    enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    user_id INT COMMENT '创建者ID',
    FOREIGN KEY (user_id) REFERENCES users(id)
) COMMENT '阈值设置表';

-- 插入一些默认的阈值设置数据
INSERT INTO threshold_settings (name, type, operator, threshold, enabled)
VALUES 
    ('高温警报', 'temperature', '>', 30, TRUE),
    ('低温警报', 'temperature', '<', 10, TRUE),
    ('湿度过高警报', 'humidity', '>', 80, TRUE),
    ('湿度过低警报', 'humidity', '<', 30, TRUE),
    ('土壤湿度过低警报', 'soil_moisture', '<', 20, TRUE);

-- 创建默认管理员账户
INSERT INTO users (username, password_hash, email, role) 
VALUES ('admin', 
        'pbkdf2:sha256:260000$YOUR_SALT$YOUR_HASH',  -- 这里会被Python代码中的真实密码哈希替换
        'admin@example.com', 
        'admin');

-- 初始化设备状态
INSERT INTO device_status (device_type, status, description) VALUES
    ('external_shade', FALSE, '外遮阳系统'),
    ('internal_shade', FALSE, '内遮阳系统'),
    ('small_vent', FALSE, '小通风设备'),
    ('internal_vent', FALSE, '内通风设备'),
    ('irrigation', FALSE, '喷灌系统'),
    ('water_curtain', FALSE, '水帘系统');