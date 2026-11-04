package com.smartagriculture.util;

import java.util.LinkedHashMap;
import java.util.Map;

public final class Maps {

    private Maps() {
    }

    /**
     * 构建有序 Map，允许 null 值。
     */
    public static Map<String, Object> of(Object... keyValues) {
        Map<String, Object> map = new LinkedHashMap<>();
        for (int i = 0; i + 1 < keyValues.length; i += 2) {
            map.put(String.valueOf(keyValues[i]), keyValues[i + 1]);
        }
        return map;
    }
}
