package com.smartagriculture.service;

import com.smartagriculture.model.OperationLog;
import com.smartagriculture.util.SensorKeys;
import com.smartagriculture.model.ThresholdSetting;
import com.smartagriculture.repository.OperationLogRepository;
import com.smartagriculture.repository.SensorDataRepository;
import com.smartagriculture.repository.ThresholdSettingRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 监测服务：根据阈值设置检查传感器数据并生成告警。
 */
@Service
public class MonitorService {

    private static final Logger log = LoggerFactory.getLogger(MonitorService.class);

    private final SensorDataRepository sensorDataRepository;
    private final ThresholdSettingRepository thresholdSettingRepository;
    private final OperationLogRepository operationLogRepository;

    public MonitorService(SensorDataRepository sensorDataRepository,
                          ThresholdSettingRepository thresholdSettingRepository,
                          OperationLogRepository operationLogRepository) {
        this.sensorDataRepository = sensorDataRepository;
        this.thresholdSettingRepository = thresholdSettingRepository;
        this.operationLogRepository = operationLogRepository;
    }

    private final java.util.Set<String> activeAlerts = new java.util.HashSet<>();

    private static String alertKey(ThresholdSetting rule) {
        return rule.id + ":" + rule.name + ":" + rule.type + ":" + rule.operator + ":" + rule.threshold;
    }

    public synchronized void checkThresholds(Map<String, Double> sensorData) {
        List<ThresholdSetting> settings = thresholdSettingRepository.findEnabled();
        activeAlerts.retainAll(settings.stream().map(MonitorService::alertKey).collect(java.util.stream.Collectors.toSet()));
        for (ThresholdSetting setting : settings) {
            checkSingleThreshold(setting, sensorData);
        }
    }

    private void checkSingleThreshold(ThresholdSetting setting, Map<String, Double> sensorData) {
        Double value = sensorData.get(SensorKeys.canonical(setting.type));
        if (value == null || !Double.isFinite(value)) {
            return;
        }
        double threshold = setting.threshold != null ? setting.threshold : 0.0;
        boolean triggered = switch (setting.operator) {
            case ">" -> value > threshold;
            case "<" -> value < threshold;
            case ">=" -> value >= threshold;
            case "<=" -> value <= threshold;
            case "==" -> value == threshold;
            default -> false;
        };
        String key = alertKey(setting);
        if (!triggered) {
            activeAlerts.remove(key);
            return;
        }
        if (activeAlerts.contains(key)) return;
        log.warn("触发阈值告警: {} 当前值 {} {} 阈值 {}", setting.name, value, setting.operator, threshold);
        try {
            OperationLog logEntry = new OperationLog();
            logEntry.operation_type = "警报";
            logEntry.device_type = null;
            logEntry.operation_time = LocalDateTime.now();
            logEntry.operation_result = false;
            logEntry.description = setting.name + ": " + setting.type + " 当前值 " + value
                    + " " + setting.operator + " 阈值 " + threshold;
            operationLogRepository.insert(logEntry);
            activeAlerts.add(key);
        } catch (Exception e) {
            log.error("记录告警日志失败: {}", e.getMessage());
        }
        // 告警只记录和通知；设备动作由独立控制器统一判断。
    }
}
