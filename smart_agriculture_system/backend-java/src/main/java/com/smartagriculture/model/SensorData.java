package com.smartagriculture.model;

import com.smartagriculture.util.Maps;

import java.time.LocalDateTime;
import java.util.Map;

public class SensorData {

    public Integer id;
    public LocalDateTime timestamp;
    public Double air_temperature;
    public Double air_humidity;
    public Double soil_temperature;
    public Double soil_moisture;
    public Double light_intensity;
    public Double co2_concentration;

    public static SensorData of(Map<String, Double> data, LocalDateTime timestamp) {
        SensorData record = new SensorData();
        record.timestamp = timestamp;
        record.air_temperature = data.getOrDefault("air_temperature", 0.0);
        record.air_humidity = data.getOrDefault("air_humidity", 0.0);
        record.soil_temperature = data.getOrDefault("soil_temperature", 0.0);
        record.soil_moisture = data.getOrDefault("soil_moisture", 0.0);
        record.light_intensity = data.getOrDefault("light_intensity", 0.0);
        record.co2_concentration = data.getOrDefault("co2_concentration", 0.0);
        return record;
    }

    public Map<String, Object> toMap() {
        return Maps.of(
                "id", id,
                "timestamp", timestamp != null ? timestamp.toString() : null,
                "air_temperature", air_temperature,
                "air_humidity", air_humidity,
                "soil_temperature", soil_temperature,
                "soil_moisture", soil_moisture,
                "light_intensity", light_intensity,
                "co2_concentration", co2_concentration,
                // 兼容字段，与前端字段对应
                "temperature", air_temperature,
                "humidity", air_humidity,
                "co2_level", co2_concentration
        );
    }
}
