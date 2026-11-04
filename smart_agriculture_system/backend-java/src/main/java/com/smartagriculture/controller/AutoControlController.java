package com.smartagriculture.controller;

import com.smartagriculture.device.AutoControlManager;
import com.smartagriculture.util.Maps;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/auto-control")
public class AutoControlController {

    private static final Logger log = LoggerFactory.getLogger(AutoControlController.class);

    private final AutoControlManager autoControlManager;

    public AutoControlController(AutoControlManager autoControlManager) {
        this.autoControlManager = autoControlManager;
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> status() {
        boolean enabled = autoControlManager.isEnabled();
        return ResponseEntity.ok(Maps.of(
                "enabled", enabled,
                "thresholds", autoControlManager.getThresholds(),
                "message", enabled ? "自动控制已启用" : "自动控制未启用"
        ));
    }

    @PostMapping("/enable")
    public ResponseEntity<Map<String, Object>> enable() {
        autoControlManager.start();
        return ResponseEntity.ok(Maps.of("message", "自动控制已启用", "enabled", true));
    }

    @PostMapping("/disable")
    public ResponseEntity<Map<String, Object>> disable() {
        autoControlManager.stop();
        return ResponseEntity.ok(Maps.of("message", "自动控制已关闭", "enabled", false));
    }

    @GetMapping("/thresholds")
    public ResponseEntity<?> thresholds() {
        return ResponseEntity.ok(autoControlManager.getThresholds());
    }

    @PostMapping("/thresholds")
    public ResponseEntity<Map<String, Object>> updateThresholds(@RequestBody(required = false) Map<String, Object> data) {
        try {
            if (data == null || data.isEmpty()) {
                return ResponseEntity.badRequest().body(Maps.of("error", "无效的请求数据"));
            }
            Object nested = data.get("thresholds");
            Map<?, ?> source = nested instanceof Map<?, ?> map ? map : data;

            Map<String, double[]> newThresholds = new LinkedHashMap<>();
            for (Map.Entry<?, ?> entry : source.entrySet()) {
                if (!(entry.getValue() instanceof Map<?, ?> range)) {
                    continue;
                }
                Object min = range.get("min");
                Object max = range.get("max");
                if (min == null || max == null) {
                    continue;
                }
                newThresholds.put(String.valueOf(entry.getKey()), new double[]{
                        toDouble(min, 0.0), toDouble(max, 0.0)
                });
            }
            if (newThresholds.isEmpty()) {
                return ResponseEntity.badRequest().body(Maps.of("error", "无有效阈值数据"));
            }
            boolean updated = autoControlManager.updateThresholds(newThresholds);
            if (!updated) {
                return ResponseEntity.badRequest().body(Maps.of("error", "阈值更新失败"));
            }
            return ResponseEntity.ok(Maps.of(
                    "message", "阈值设置已更新",
                    "thresholds", autoControlManager.getThresholds()
            ));
        } catch (Exception e) {
            log.error("更新阈值设置失败: {}", e.getMessage());
            return ResponseEntity.status(500).body(Maps.of("error", "更新阈值设置失败: " + e.getMessage()));
        }
    }

    private static double toDouble(Object value, double defaultValue) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        try {
            return Double.parseDouble(String.valueOf(value));
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }
}
