package com.smartagriculture.model;

import com.smartagriculture.util.Maps;

import java.time.LocalDateTime;
import java.util.Map;

public class ThresholdSetting {

    public Integer id;
    public String name;
    public String type;
    public String operator;
    public Double threshold;
    public Boolean enabled;
    public LocalDateTime create_time;
    public LocalDateTime update_time;
    public Integer user_id;

    public Map<String, Object> toMap() {
        return Maps.of(
                "id", id,
                "name", name,
                "type", type,
                "operator", operator,
                "threshold", threshold,
                "enabled", enabled,
                "create_time", create_time != null ? create_time.toString() : null,
                "update_time", update_time != null ? update_time.toString() : null,
                "user_id", user_id
        );
    }
}
