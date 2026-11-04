# 智能农业系统 - 后端

## 项目概述

智能农业系统后端是基于Python Flask框架开发的RESTful API服务，负责设备控制、数据采集、存储和分析。系统通过TCP/IP协议与虚拟硬件平台通信，控制温室内的各种设备，如通风系统、喷灌系统、天窗、水帘和照明等，同时实时监测温室内的温度、湿度、光照强度和CO2浓度等环境参数。

## 技术栈

- **编程语言**: Python 3.x
- **Web框架**: Flask
- **数据库**: MySQL + SQLAlchemy ORM
- **认证**: JWT (JSON Web Tokens)
- **通信协议**: TCP/IP

## 主要功能

1. **设备控制模块**
   - 控制各类温室设备（通风系统、喷灌系统、天窗、水帘和照明等）
   - 提供RESTful API接口供前端调用
   - 支持手动控制和自动控制模式

2. **数据采集模块**
   - 实时采集温室环境参数（温度、湿度、光照、CO2浓度等）
   - 数据持久化存储
   - 提供历史数据查询接口

3. **告警系统**
   - 基于阈值的实时监控
   - 异常数据检测和告警通知
   - 自定义告警规则配置
   - 自动控制响应（当触发警报时自动控制相关设备）

4. **用户认证与授权**
   - JWT认证
   - 角色权限控制
   - 操作日志记录

## 项目结构

```
backend/
├── app.py                 # 应用入口
├── config/                # 配置文件
│   ├── database.py        # 数据库配置
│   ├── hardware_config.py # 硬件设备配置
│   └── logging_config.py  # 日志配置
├── device/                # 设备控制模块
│   ├── device_manager.py  # 设备管理器
│   └── wsn_client.py      # 无线传感网客户端
├── models/                # 数据模型
│   ├── device_status.py   # 设备状态模型
│   ├── operation_log.py   # 操作日志模型
│   ├── sensor_data.py     # 传感器数据模型
│   └── user.py            # 用户模型
├── routes/                # API路由
│   ├── alerts.py          # 告警相关路由
│   ├── auth.py            # 认证相关路由
│   ├── device_control.py  # 设备控制路由
│   └── history.py         # 历史数据路由
├── services/              # 业务逻辑
│   ├── auth_service.py    # 认证服务
│   ├── monitor_service.py # 监控服务
│   └── auto_control_service.py # 自动控制服务
├── create_threshold_table.py # 阈值表创建脚本
├── init_db.sql            # 数据库初始化SQL
└── requirements.txt       # 依赖包清单
```

## API接口

### 认证接口
- `POST /api/auth/login`: 用户登录
- `POST /api/auth/logout`: 用户登出

### 设备控制接口
- `GET /api/device/status`: 获取设备状态
- `POST /api/device/control`: 控制设备
- `GET /api/device/connection-status`: 获取设备连接状态

### 传感器数据接口
- `GET /api/sensor-data`: 获取实时传感器数据
- `GET /api/history/sensor-data`: 获取历史传感器数据

### 告警接口
- `GET /api/alerts`: 获取告警信息
- `GET /api/alerts/rules`: 获取告警规则
- `POST /api/alerts/rules`: 创建告警规则
- `PUT /api/alerts/rules/<id>`: 更新告警规则
- `DELETE /api/alerts/rules/<id>`: 删除告警规则
- `PUT /api/alerts/rules/<id>/toggle`: 启用/禁用告警规则
- `GET /api/alerts/auto-control/rules`: 获取自动控制规则
- `GET /api/alerts/auto-control/logs`: 获取自动控制日志

## 安装与部署

1. 安装依赖包:
```bash
pip install -r requirements.txt
```

2. 配置数据库:
```bash
mysql -u root -p < init_db.sql
```

3. 启动服务:
```bash
python app.py
```

## 系统配置

### 数据采集频率

系统配置为每**2分钟**采集一次传感器数据，以减少不必要的数据存储和处理负担。此频率适用于农业环境监测，因为农业环境参数通常变化缓慢。

### 自动控制规则

系统内置了一系列自动控制规则，当传感器数据触发警报阈值时，系统会自动控制相关设备进行环境调节：

- 当温度 > 50°C：自动开启外部风扇、内部风扇、外遮阳、内遮阳和天窗
- 当温度 < 10°C：自动关闭外部风扇、内部风扇、外遮阳和内遮阳
- 当湿度 > 80%：自动关闭水帘和喷灌系统
- 当湿度 < 30%：自动开启水帘和喷灌系统
- 当土壤湿度 < 20%：自动开启喷灌系统
- 当土壤湿度 > 80%：自动关闭喷灌系统
- 当光照强度 < 1000 lux：自动开启灯光
- 当光照强度 > 8000 lux：自动开启外遮阳和内遮阳
- 当CO2浓度 > 3000 ppm：自动开启天窗、外部风扇和内部风扇

## 硬件连接配置

系统通过TCP/IP协议与虚拟硬件平台通信，默认连接设置:

- 控制器IP: 192.168.133.1
- 控制器端口: 4000

设备继电器配置:
- 继电器1 (地址: 0x2001)
  - 端口1: 外部通风系统
  - 端口2: 内部通风系统
- 继电器2 (地址: 0x2003)
  - 端口1: 天窗控制
  - 端口2: 喷灌系统
  - 端口3: 水帘系统
  - 端口4: 照明系统