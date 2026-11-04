package com.smartagriculture.device;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 自动控制管理器：按温湿度、光照、CO2 阈值自动开关设备，每 30 秒执行一次。
 */
@Component
public class AutoControlManager {

    private static final Logger log = LoggerFactory.getLogger(AutoControlManager.class);

    private final DeviceManager deviceManager;

    private final Map<String, double[]> thresholds = new LinkedHashMap<>();
    private final Map<String, String> deviceMapping = new LinkedHashMap<>();

    private volatile boolean running = false;
    private Thread controlThread;

    public AutoControlManager(DeviceManager deviceManager) {
        this.deviceManager = deviceManager;

        thresholds.put("temperature", new double[]{15, 30});
        thresholds.put("humidity", new double[]{40, 80});
        thresholds.put("light", new double[]{5000, 20000});
        thresholds.put("co2", new double[]{400, 1000});

        deviceMapping.put("temperature", "water_curtain");
        deviceMapping.put("humidity", "internal_fan");
        deviceMapping.put("light", "light");
        deviceMapping.put("co2", "external_fan");
    }

    public synchronized void start() {
        if (running) {
            log.info("自动控制已经开启");
            return;
        }
        running = true;
        controlThread = new Thread(this::controlLoop, "auto-control");
        controlThread.setDaemon(true);
        controlThread.start();
        log.info("自动控制已启动");
    }

    public synchronized void stop() {
        if (!running) {
            log.info("自动控制已经关闭");
            return;
        }
        running = false;
        if (controlThread != null) {
            controlThread.interrupt();
            controlThread = null;
        }
        log.info("自动控制已停止");
    }

    public boolean isEnabled() {
        return running;
    }

    public synchronized Map<String, Map<String, Double>> getThresholds() {
        Map<String, Map<String, Double>> result = new LinkedHashMap<>();
        for (Map.Entry<String, double[]> entry : thresholds.entrySet()) {
            Map<String, Double> range = new LinkedHashMap<>();
            range.put("min", entry.getValue()[0]);
            range.put("max", entry.getValue()[1]);
            result.put(entry.getKey(), range);
        }
        return result;
    }

    public synchronized boolean updateThresholds(Map<String, double[]> newThresholds) {
        if (newThresholds == null || newThresholds.isEmpty()) {
            return false;
        }
        for (Map.Entry<String, double[]> entry : newThresholds.entrySet()) {
            if (entry.getValue() == null || entry.getValue().length < 2) {
                continue;
            }
            double min = entry.getValue()[0];
            double max = entry.getValue()[1];
            if (min >= max) {
                log.warn("阈值设置无效: {} 最小值 {} 大于等于最大值 {}", entry.getKey(), min, max);
                continue;
            }
            thresholds.put(entry.getKey(), new double[]{min, max});
        }
        log.info("阈值设置已更新: {}", thresholds.keySet());
        return true;
    }

    private void controlLoop() {
        while (running) {
            try {
                if (!deviceManager.getWsnClient().isConnected()) {
                    log.info("自动控制：设备未连接，尝试重新连接");
                    deviceManager.connect();
                }
                Map<String, Double> sensorData = deviceManager.getSensorData();
                if (!sensorData.isEmpty()) {
                    checkThresholds(sensorData);
                }
            } catch (Exception e) {
                log.error("自动控制执行失败: {}", e.getMessage());
            }
            try {
                Thread.sleep(30_000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    private synchronized void checkThresholds(Map<String, Double> sensorData) {
        Double temperature = sensorData.get("air_temperature");
        if (temperature != null) {
            double[] range = thresholds.get("temperature");
            if (range != null && (temperature < range[0] || temperature > range[1])) {
                String action = temperature > range[1] ? "open" : "close";
                deviceManager.controlDevice(deviceMapping.get("temperature"), action);
            }
        }

        Double humidity = sensorData.get("air_humidity");
        if (humidity != null) {
            double[] range = thresholds.get("humidity");
            if (range != null && (humidity < range[0] || humidity > range[1])) {
                String action = humidity > range[1] ? "open" : "close";
                deviceManager.controlDevice(deviceMapping.get("humidity"), action);
            }
        }

        Double light = sensorData.get("light_intensity");
        if (light != null) {
            double[] range = thresholds.get("light");
            if (range != null && (light < range[0] || light > range[1])) {
                String action = light < range[0] ? "open" : "close";
                deviceManager.controlDevice(deviceMapping.get("light"), action);
            }
        }

        Double co2 = sensorData.get("co2_concentration");
        if (co2 != null) {
            double[] range = thresholds.get("co2");
            if (range != null && (co2 < range[0] || co2 > range[1])) {
                String action = co2 > range[1] ? "open" : "close";
                deviceManager.controlDevice(deviceMapping.get("co2"), action);
            }
        }
    }
}
