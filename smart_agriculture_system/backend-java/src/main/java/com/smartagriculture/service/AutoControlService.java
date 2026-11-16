package com.smartagriculture.service;

import com.smartagriculture.device.AutoControlManager;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Map;

/** 兼容告警页面的规则读取接口，规则由独立控制器提供。 */
@Service
public class AutoControlService {
    private final AutoControlManager manager;
    public AutoControlService(AutoControlManager manager) { this.manager = manager; }
    public Map<String, List<Map<String, Object>>> getControlRules() {
        return manager.getControlRules();
    }
}
