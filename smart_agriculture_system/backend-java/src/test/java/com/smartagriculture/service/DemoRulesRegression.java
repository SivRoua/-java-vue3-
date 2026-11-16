package com.smartagriculture.service;

import com.smartagriculture.device.DeviceManager;
import com.smartagriculture.model.OperationLog;
import com.smartagriculture.model.ThresholdSetting;
import com.smartagriculture.repository.OperationLogRepository;
import com.smartagriculture.repository.SensorDataRepository;
import com.smartagriculture.repository.ThresholdSettingRepository;
import com.smartagriculture.util.SensorKeys;
import java.util.List;
import java.util.Map;

/** Standalone offline regression; no WSN or MySQL access. */
public class DemoRulesRegression {
    static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
    static class Devices extends DeviceManager {
        boolean result = true;
        int calls;
        @Override public synchronized boolean controlDevice(String type, String action) { calls++; return result; }
    }
    static class Logs extends OperationLogRepository {
        int alerts;
        Logs() { super(null); }
        @Override public int insert(OperationLog entry) { if ("警报".equals(entry.operation_type)) alerts++; return 1; }
    }
    static class Rules extends ThresholdSettingRepository {
        ThresholdSetting current = new ThresholdSetting();
        Rules() { super(null); }
        @Override public List<ThresholdSetting> findEnabled() { return List.of(current); }
    }
    public static void main(String[] args) {
        Devices devices = new Devices();
        Logs logs = new Logs();
        Rules rules = new Rules();
        MonitorService monitor = new MonitorService(new SensorDataRepository(null), rules, logs);
        String[][] aliases = {{"temperature","air_temperature"},{"humidity","air_humidity"},
            {"co2_level","co2_concentration"},{"soil_moisture","soil_moisture"},
            {"soil_temperature","soil_temperature"},{"light_intensity","light_intensity"}};
        for (String[] alias : aliases) {
            check(SensorKeys.canonical(alias[0]).equals(alias[1]), "alias mismatch");
            rules.current.type = alias[0]; rules.current.operator = ">"; rules.current.threshold = 10.0;
            int before = logs.alerts;
            monitor.checkThresholds(Map.of(alias[1], 20.0));
            check(logs.alerts == before + 1, "legacy metric did not trigger: " + alias[0]);
        }
        rules.current.type = "air_temperature";
        for (String op : List.of(">", "<", ">=", "<=", "==")) {
            rules.current.operator = op; rules.current.threshold = 20.0;
            int before = logs.alerts;
            monitor.checkThresholds(Map.of("air_temperature", 20.0));
            boolean expected = List.of(">=", "<=", "==").contains(op);
            check(logs.alerts == before + (expected ? 1 : 0), "comparison boundary failed: " + op);
        }
        rules.current.operator = ">"; rules.current.threshold = 50.0;
        int beforeEpisode = logs.alerts;
        monitor.checkThresholds(Map.of("air_temperature", 60.0));
        monitor.checkThresholds(Map.of("air_temperature", 65.0));
        check(logs.alerts == beforeEpisode + 1, "continuous threshold breach created duplicate alerts");
        monitor.checkThresholds(Map.of("air_temperature", 40.0));
        monitor.checkThresholds(Map.of("air_temperature", 60.0));
        check(logs.alerts == beforeEpisode + 2, "recovered metric failed to start a new alert episode");
        check(devices.calls == 0, "alerts must not send device commands");
        System.out.println("Demo rule regressions passed without hardware/database.");
    }
}
