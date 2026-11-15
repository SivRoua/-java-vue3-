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
        AutoControlService automatic = new AutoControlService(devices, logs);
        MonitorService monitor = new MonitorService(new SensorDataRepository(null), rules, logs, automatic);
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
        int before = devices.calls;
        check(automatic.handleAlert("air_temperature", 30), "raw temperature rule failed");
        check(automatic.handleAlert("air_humidity", 90), "raw humidity rule failed");
        check(automatic.handleAlert("light_intensity", 100), "raw light rule failed");
        check(automatic.handleAlert("co2_concentration", 2000), "raw CO2 rule failed");
        check(devices.calls == before + 4, "unexpected command count");
        devices.result = false;
        check(!automatic.handleAlert("temperature", 30), "failed control reported success");
        check(!automatic.handleAlert(null, 30), "null type accepted");
        System.out.println("Demo rule regressions passed without hardware/database.");
    }
}
