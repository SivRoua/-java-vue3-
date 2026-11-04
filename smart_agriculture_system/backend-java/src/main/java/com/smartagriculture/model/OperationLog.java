package com.smartagriculture.model;

import java.time.LocalDateTime;

public class OperationLog {

    public Integer id;
    public Integer user_id;
    public String operation_type;
    public String device_type;
    public LocalDateTime operation_time;
    public Boolean operation_result;
    public String description;
}
