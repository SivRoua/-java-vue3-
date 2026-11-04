# 传感器配置
SENSOR_CONFIG = {
    'air_temperature': {    # 空气温度传感器
        'range': (-25, 50), # 测量范围：-25°C 到 50°C
        'unit': '°C'        # 单位
    },
    'air_humidity': {       # 空气湿度传感器
        'range': (0, 100),  # 测量范围：0% 到 100%
        'unit': '%'
    },
    'soil_temperature': {   # 土壤温度传感器
        'range': (-10, 50), # 测量范围：-10°C 到 50°C
        'unit': '°C'
    },
    'soil_moisture': {      # 土壤湿度传感器
        'range': (0, 100),  # 测量范围：0% 到 100%
        'unit': '%'
    },
    'light_intensity': {    # 光照强度传感器
        'range': (0, 10000),# 测量范围：0 到 10000 lux
        'unit': 'lux'
    },
    'co2_concentration': {  # CO2浓度传感器
        'range': (0, 5000), # 测量范围：0 到 5000 ppm
        'unit': 'ppm'
    },
    'ph_value': {           # pH值传感器
        'range': (0, 14),   # 测量范围：0 到 14
        'unit': ''          # 无单位
    }
}

# 设备配置
# 注意：relay_port 是从1开始的端口号，在代码中使用时需要转换为从0开始的索引
DEVICE_CONFIG = {
    'external_shade': {
        'name': '外遮阳',
        'type': 'binary',  # 二进制控制（开/关）
        'default': 'close',
        'description': '控制温室外部遮阳系统',
        'relay_address': 0x2001,  # 继电器1地址
        'relay_port': 1           # 继电器1的第1个端口 (索引为0)
    },
    'internal_shade': {
        'name': '内遮阳',
        'type': 'binary',
        'default': 'close',
        'description': '控制温室内部遮阳系统',
        'relay_address': 0x2001,  # 继电器1地址
        'relay_port': 2           # 继电器1的第2个端口 (索引为1)
    },
    'skylight': {
        'name': '天窗',
        'type': 'binary',
        'default': 'close',
        'description': '控制温室顶部天窗',
        'relay_address': 0x2003,  # 继电器2地址
        'relay_port': 1           # 继电器2的第1个端口 (索引为0)
    },
    'spray': {
        'name': '喷灌',
        'type': 'binary',
        'default': 'close',
        'description': '控制温室喷灌系统',
        'relay_address': 0x2003,  # 继电器2地址
        'relay_port': 2           # 继电器2的第2个端口 (索引为1)
    },
    'water_curtain': {
        'name': '水帘',
        'type': 'binary',
        'default': 'close',
        'description': '控制温室水帘系统',
        'relay_address': 0x2003,  # 继电器2地址
        'relay_port': 3           # 继电器2的第3个端口 (索引为2)
    },
    'light': {
        'name': '灯光',
        'type': 'binary',
        'default': 'close',
        'description': '控制温室照明系统',
        'relay_address': 0x2003,  # 继电器2地址
        'relay_port': 4           # 继电器2的第4个端口 (索引为3)
    },
    'external_fan': {
        'name': '外通风',
        'type': 'binary',
        'default': 'close',
        'description': '控制温室外部通风系统',
        'relay_address': 0x2001,  # 继电器1地址
        'relay_port': 3           # 继电器1的第3个端口 (索引为2)
    },
    'internal_fan': {
        'name': '内通风',
        'type': 'binary',
        'default': 'close',
        'description': '控制温室内部通风系统',
        'relay_address': 0x2001,  # 继电器1地址
        'relay_port': 4           # 继电器1的第4个端口 (索引为3)
    }
}

# 硬件通信配置
HARDWARE_CONFIG = {
    'controller': {
        'ip': '192.168.12.1',
        'port': 4000,
        'timeout': 3,  # 连接超时时间（秒），减少以提高响应速度
        'retry': 5     # 增加重试次数，提高连接成功率
    }
}

# 继电器配置
RELAY_CONFIG = {
    0x2001: {  # 继电器1地址
        'name': '继电器1',
        'ports': 4,  # 端口数量
        'devices': ['external_shade', 'internal_shade', 'external_fan', 'internal_fan']  # 连接的设备
    },
    0x2003: {  # 继电器2地址
        'name': '继电器2',
        'ports': 4,  # 端口数量
        'devices': ['skylight', 'spray', 'water_curtain', 'light']  # 连接的设备
    }
}

# 继电器命令格式说明
# 查询命令: A5 02 addr_high addr_low 00 00 00 00 00 5A
# 控制命令: A5 01 addr_high addr_low status1 status2 status3 status4 00 5A
# 其中status: 1=开启，0=关闭

# 传感器数据格式说明
# 格式: B5 type addr data1 data2 data3 data4 data5 5B
# type: 0x31=温度, 0x32=湿度, 0x33=CO2, 0x34=光照