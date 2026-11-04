package com.smartagriculture.service;

import com.smartagriculture.device.DeviceManager;
import com.smartagriculture.model.OperationLog;
import com.smartagriculture.repository.OperationLogRepository;
import com.smartagriculture.util.Maps;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 自动控制服务：根据传感器数值匹配控制规则并执行设备操作。
 */
@Service
public class AutoControlService {

    private static final Logger log = LoggerFactory.getLogger(AutoControlService.class);

    private final DeviceManager deviceManager;
    private final OperationLogRepository operationLogRepository;

    private final Map<String, List<Map<String, Object>>> controlRules = new LinkedHashMap<>();

    public AutoControlService(DeviceManager deviceManager, OperationLogRepository operationLogRepository) {
        this.deviceManager = deviceManager;
        this.operationLogRepository = operationLogRepository;
        initControlRules();
    }

    private void initControlRules() {
        List<Map<String, Object>> temperature = new ArrayList<>();
        temperature.add(Maps.of("threshold_operator", ">", "threshold_value", 28.0,
                "device_type", "water_curtain", "action", "open",
                "description", "温度过高，开启水帘降温"));
        temperature.add(Maps.of("threshold_operator", "<", "threshold_value", 15.0,
                "device_type", "water_curtain", "action", "close",
                "description", "温度过低，关闭水帘"));
        controlRules.put("temperature", temperature);

        List<Map<String, Object>> humidity = new ArrayList<>();
        humidity.add(Maps.of("threshold_operator", ">", "threshold_value", 85.0,
                "device_type", "internal_fan", "action", "open",
                "description", "湿度过高，开启内通风"));
        humidity.add(Maps.of("threshold_operator", "<", "threshold_value", 40.0,
                "device_type", "internal_fan", "action", "close",
                "description", "湿度过低，关闭内通风"));
        controlRules.put("humidity", humidity);

        List<Map<String, Object>> light = new ArrayList<>();
        light.add(Maps.of("threshold_operator", "<", "threshold_value", 5000.0,
                "device_type", "light", "action", "open",
                "description", "光照不足，开启补光灯"));
        light.add(Maps.of("threshold_operator", ">", "threshold_value", 25000.0,
                "device_type", "light", "action", "close",
                "description", "光照过强，关闭补光灯"));
        controlRules.put("light", light);

        List<Map<String, Object>> co2 = new ArrayList<>();
        co2.add(Maps.of("threshold_operator", ">", "threshold_value", 1500.0,
                "device_type", "external_fan", "action", "open",
                "description", "CO2浓度过高，开启外通风"));
        controlRules.put("co2", co2);
    }

    public Map<String, List<Map<String, Object>>> getControlRules() {
        return new LinkedHashMap<>(controlRules);
    }

    /**
     * 处理告警并执行匹配的自动控制规则。
     */
    public boolean handleAlert(String thresholdType, double value) {
        List<Map<String, Object>> rules = controlRules.get(thresholdType);
        if (rules == null || rules.isEmpty()) {
            log.warn("未找到 {} 的控制规则", thresholdType);
            return false;
        }
        for (Map<String, Object> rule : rules) {
            String operator = String.valueOf(rule.get("threshold_operator"));
            double thresholdValue = ((Number) rule.get("threshold_value")).doubleValue();
            boolean matched = (">".equals(operator) && value > thresholdValue)
                    || ("<".equals(operator) && value < thresholdValue);
            if (!matched) {
                continue;
            }
            String deviceType = String.valueOf(rule.get("device_type"));
            String action = String.valueOf(rule.get("action"));
            String description = String.valueOf(rule.get("description"));
            boolean success = deviceManager.controlDevice(deviceType, action);
            log.info("{} - 设备 {} 执行 {} 操作: {}", description, deviceType, action,
                    success ? "成功" : "失败");
            logAutoControl(deviceType, description + "，操作结果: " + (success ? "成功" : "失败"), success);
            return true;
        }
        return false;
    }

    private void logAutoControl(String deviceType, String description, boolean success) {
        try {
            OperationLog logEntry = new OperationLog();
            logEntry.operation_type = "自动控制";
            logEntry.device_type = deviceType;
            logEntry.operation_time = LocalDateTime.now();
            logEntry.operation_result = success;
            logEntry.description = description;
            operationLogRepository.insert(logEntry);
        } catch (Exception e) {
            log.error("记录自动控制日志失败: {}", e.getMessage());
        }
    }
}
