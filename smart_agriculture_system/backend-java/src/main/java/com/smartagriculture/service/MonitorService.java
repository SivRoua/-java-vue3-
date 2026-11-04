package com.smartagriculture.service;

import com.smartagriculture.model.OperationLog;
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
    private final AutoControlService autoControlService;

    public MonitorService(SensorDataRepository sensorDataRepository,
                          ThresholdSettingRepository thresholdSettingRepository,
                          OperationLogRepository operationLogRepository,
                          AutoControlService autoControlService) {
        this.sensorDataRepository = sensorDataRepository;
        this.thresholdSettingRepository = thresholdSettingRepository;
        this.operationLogRepository = operationLogRepository;
        this.autoControlService = autoControlService;
    }

    public void checkThresholds(Map<String, Double> sensorData) {
        List<ThresholdSetting> settings = thresholdSettingRepository.findEnabled();
        for (ThresholdSetting setting : settings) {
            checkSingleThreshold(setting, sensorData);
        }
    }

    private void checkSingleThreshold(ThresholdSetting setting, Map<String, Double> sensorData) {
        Double value = sensorData.get(setting.type);
        if (value == null) {
            return;
        }
        double threshold = setting.threshold != null ? setting.threshold : 0.0;
        boolean triggered = ">".equals(setting.operator) ? value > threshold
                : "<".equals(setting.operator) && value < threshold;
        if (!triggered) {
            return;
        }
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
        } catch (Exception e) {
            log.error("记录告警日志失败: {}", e.getMessage());
        }
        autoControlService.handleAlert(setting.type, value);
    }
}
