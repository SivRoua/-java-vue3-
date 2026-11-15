package com.smartagriculture.util;

/** 兼容已有告警规则与采集读数的指标名称，不迁移数据库。 */
public final class SensorKeys {
    private SensorKeys() { }

    public static String canonical(String type) {
        if (type == null) return null;
        return switch (type) {
            case "temperature" -> "air_temperature";
            case "humidity" -> "air_humidity";
            case "light" -> "light_intensity";
            case "co2", "co2_level" -> "co2_concentration";
            default -> type;
        };
    }
}
