from flask import Flask, jsonify, request, redirect, make_response
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config.database import Config, init_db, shutdown_session
from config.logging_config import LOGGING_CONFIG
from config.settings import JWT_SECRET_KEY
from routes.auth import auth_bp
from routes.users import users_bp
from routes.device_control import device_bp
from routes.auto_control import auto_control_bp
from routes.history import history_bp
from routes.alerts import alerts_bp
import logging.config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.sensor_data import SensorData
from models.device_status import DeviceStatus
from models.operation_log import OperationLog
from device.device_manager import DeviceManager
from services.monitor_service import MonitorService
from services.auto_control_service import AutoControlService
import threading
import time
import json
from datetime import datetime, timedelta
from extensions import db, jwt, init_extensions

# 配置日志
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 初始化扩展
init_extensions(app)

# JWT配置
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'

# 初始化JWT
jwt = JWTManager(app)

# 自定义JWT错误处理
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'status': 'error',
        'message': 'Token已过期'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'status': 'error',
        'message': 'Token无效'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'status': 'error',
        'message': '缺少Token'
    }), 401

# 启用 Flask-CORS，配置跨域
CORS(app, 
     resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]}}, 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "Accept"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Content-Type", "Authorization"])

# 创建设备管理器实例
device_manager = DeviceManager()

# 创建自动控制服务实例
auto_control_service = AutoControlService(device_manager)

# 创建监控服务实例，并传入自动控制服务
monitor_service = MonitorService(auto_control_service)

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(users_bp, url_prefix='/api')
app.register_blueprint(device_bp, url_prefix='/api/device')
app.register_blueprint(auto_control_bp, url_prefix='/api/auto-control')
app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
app.register_blueprint(history_bp, url_prefix='/api/history')

# 全局OPTIONS处理
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return '', 204

# 添加向后兼容的路由
@app.route('/sensor-data')
def sensor_data_compatibility():
    # 从数据库获取传感器数据，如果没有则从虚拟平台获取并存入数据库
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 获取最新的传感器数据
        latest_data = session.query(SensorData).order_by(SensorData.timestamp.desc()).first()
        
        # 如果数据库没有数据，从虚拟平台获取
        if not latest_data:
            # 确保连接到WSN
            if not device_manager.wsn_client.connected:
                device_manager.connect()
            
            # 从虚拟平台获取数据
            sensor_data = device_manager.get_sensor_data()
            
            if not sensor_data:
                return jsonify({'error': '没有可用的传感器数据'}), 404
                
            # 存入数据库
            new_sensor_data = SensorData(
                air_temperature=sensor_data.get('air_temperature'),
                air_humidity=sensor_data.get('air_humidity'),
                soil_temperature=sensor_data.get('soil_temperature'),
                soil_moisture=sensor_data.get('soil_moisture'),
                light_intensity=sensor_data.get('light_intensity'),
                co2_concentration=sensor_data.get('co2_concentration')
            )
            session.add(new_sensor_data)
            session.commit()
            logger.info("成功将传感器数据存入数据库")
            
            return jsonify(sensor_data)
        
        # 返回数据库中的最新数据
        return jsonify(latest_data.to_dict())
    except Exception as e:
        logger.error(f"获取传感器数据失败: {str(e)}")
        session.rollback()
        return jsonify({'error': '获取传感器数据失败'}), 500
    finally:
        session.close()

@app.route('/device/status')
def device_status_compatibility():
    # 直接从设备管理器获取设备状态，绕过JWT验证
    try:
        device_type = request.args.get('device_type')
        
        # 从设备管理器获取实时状态
        device_statuses = device_manager.get_device_status()
        
        # 如果请求特定设备
        if device_type:
            if device_type in device_statuses:
                return jsonify(device_statuses[device_type])
            else:
                return jsonify({'error': f'未知设备类型: {device_type}'}), 404
        
        # 返回所有设备状态的列表
        result = []
        for device_type, status_data in device_statuses.items():
            # 确保每个设备都有正确的数据格式
            device_data = {
                'type': device_type,
                'name': status_data.get('name', device_type),
                'description': status_data.get('description', ''),
                'status': status_data.get('status', 0)
            }
            result.append(device_data)
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取设备状态失败: {str(e)}")
        return jsonify({'error': f'获取设备状态失败: {str(e)}'}), 500

@app.route('/api/device/control', methods=['POST'])
def api_device_control():
    """控制设备API路由"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': False, 'message': '无效的请求数据'}), 400
            
        device_type = data.get('device_type')
        action = data.get('action')
        
        if not device_type or not action:
            return jsonify({'status': False, 'message': '设备类型和操作不能为空'}), 400
            
        # 确保设备连接
        if not device_manager.wsn_client.connected:
            if not device_manager.connect():
                return jsonify({'status': False, 'message': '无法连接到设备控制器'}), 500
        
        # 执行设备控制
        logger.info(f"API请求控制设备: {device_type} {action}")
        result = device_manager.control_device(device_type, action)
        
        if result:
            return jsonify({
                'status': True, 
                'message': f'设备 {device_type} {action} 成功',
                'device_type': device_type,
                'action': action,
                'current_status': 1 if action.lower() == 'open' else 0
            })
        else:
            return jsonify({'status': False, 'message': f'设备 {device_type} {action} 失败'}), 500
            
    except Exception as e:
        logger.error(f"设备控制API错误: {str(e)}")
        return jsonify({'status': False, 'message': f'设备控制失败: {str(e)}'}), 500

@app.route('/device/connect', methods=['POST'])
def device_connect_compatibility():
    # 简单返回成功
    return jsonify({'message': '设备连接成功', 'status': 'connected'})

@app.route('/device/control', methods=['OPTIONS'])
def device_control_options():
    """处理设备控制的预检请求"""
    return '', 204

# 注册请求结束后的清理函数
app.teardown_appcontext(shutdown_session)

# 全局异常处理
@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理器"""
    logger.error(f"全局异常: {str(e)}")
    response = jsonify({
        "error": str(e),
        "type": e.__class__.__name__
    })
    return response, 500

def setup_app():
    """应用初始化设置"""
    # 确保在应用上下文中执行数据库初始化
    with app.app_context():
        try:
            # 初始化数据库
            init_db()
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
    
    # 额外尝试运行阈值设置表创建脚本
    try:
        from create_threshold_table import create_threshold_table
        if create_threshold_table():
            logger.info("阈值设置表已创建和初始化")
        else:
            logger.warning("阈值设置表创建或初始化存在问题")
    except Exception as e:
        logger.warning(f"创建阈值设置表时出错: {str(e)}")
    
    # 确保管理员账户存在
    from services.auth_service import AuthService
    auth_service = AuthService()
    auth_service.ensure_admin_exists()
    logger.info("确保管理员账户存在")
    
    # 启动定时监控线程
    def monitor_thread():
        """定时检查传感器数据和阈值"""
        check_count = 0
        while True:
            try:
                # 每120秒（2分钟）检查一次
                time.sleep(120)
                check_count += 1
                # 只有在第一次检查和每5次检查才输出日志（每10分钟）
                if check_count == 1 or check_count % 5 == 0:
                    logger.info(f"正在执行定时检查 (#{check_count})")
                
                # 获取最新传感器数据
                sensor_data = device_manager.get_sensor_data()
                
                if sensor_data:
                    # 存入数据库
                    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
                    Session = sessionmaker(bind=engine)
                    session = Session()
                    
                    try:
                        new_sensor_data = SensorData(
                            air_temperature=sensor_data.get('air_temperature'),
                            air_humidity=sensor_data.get('air_humidity'),
                            soil_temperature=sensor_data.get('soil_temperature'),
                            soil_moisture=sensor_data.get('soil_moisture'),
                            light_intensity=sensor_data.get('light_intensity'),
                            co2_concentration=sensor_data.get('co2_concentration')
                        )
                        session.add(new_sensor_data)
                        session.commit()
                        
                        # 检查阈值
                        result = monitor_service.check_thresholds()
                        if result:
                            logger.info("定时检查触发了警报")
                        
                    except Exception as db_error:
                        logger.error(f"存储传感器数据失败: {str(db_error)}")
                        session.rollback()
                    finally:
                        session.close()
                else:
                    logger.warning("无法获取传感器数据")
                    
            except Exception as e:
                logger.error(f"监控线程出错: {str(e)}")
                time.sleep(30)  # 出错后30秒重试
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_thread, daemon=True)
    monitor_thread.start()
    logger.info("已启动定时监控线程")
    
    # 连接到硬件控制器
    connected = device_manager.connect()
    if connected:
        logger.info(f"已连接到硬件控制器: {device_manager.wsn_client.host}:{device_manager.wsn_client.port}")
        
        # 设置定时任务每5分钟检查连接状态并自动重连
        def connection_watchdog():
            check_count = 0
            while True:
                try:
                    check_count += 1
                    if not device_manager.wsn_client.connected:
                        logger.warning("检测到设备连接已断开，尝试重新连接...")
                        device_manager.connect()
                    # 减少日志频率，只在第一次和每6次检查（1小时）输出日志
                    elif check_count == 1 or check_count % 6 == 0:
                        logger.info(f"连接监控正在运行 (#{check_count}): 连接状态正常")
                    time.sleep(600)  # 每10分钟检查一次
                except Exception as e:
                    logger.error(f"连接监控任务出错: {str(e)}")
                    time.sleep(60)  # 出错后1分钟后重试
        
        # 启动连接监控线程
        connection_thread = threading.Thread(target=connection_watchdog, daemon=True)
        connection_thread.start()
        logger.info("已启动连接监控线程，将自动维持与硬件的连接")
    else:
        logger.warning("未能连接到硬件控制器，将在需要时重试连接")
        # 继续尝试连接
        def retry_connection():
            retry_count = 0
            max_retries = 10
            while retry_count < max_retries:
                # 只在第一次、第五次和最后一次输出日志，减少日志量
                if retry_count == 0 or retry_count == 4 or retry_count == max_retries - 1:
                    logger.info(f"尝试重新连接到硬件控制器 (尝试 {retry_count+1}/{max_retries})...")
                if device_manager.connect():
                    logger.info("重连成功!")
                    break
                retry_count += 1
                time.sleep(30)  # 30秒后重试
            
            if retry_count >= max_retries:
                logger.error("多次尝试连接失败，请检查硬件控制器状态")
        
        # 启动重试线程
        retry_thread = threading.Thread(target=retry_connection, daemon=True)
        retry_thread.start()
        logger.info("已启动后台重连线程")

# 在应用上下文中执行初始化
with app.app_context():
    setup_app()

# 直接访问传感器数据的路由
@app.route('/sensor-data')
def sensor_data_direct():
    """从虚拟平台直接获取传感器数据，无需认证"""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 确保连接到WSN
        if not device_manager.wsn_client.connected:
            device_manager.connect()
        
        # 从虚拟平台获取数据
        sensor_data = device_manager.get_sensor_data()
        
        if not sensor_data:
            return jsonify({'error': '无法从虚拟平台获取传感器数据'}), 500
            
        # 只在DEBUG级别打印详细数据
        if logger.getEffectiveLevel() <= logging.DEBUG:
            logger.debug(f"API返回传感器数据: {json.dumps(sensor_data, ensure_ascii=False)}")
            
        # 存入数据库
        new_sensor_data = SensorData(
            air_temperature=sensor_data.get('air_temperature'),
            air_humidity=sensor_data.get('air_humidity'),
            soil_temperature=sensor_data.get('soil_temperature'),
            soil_moisture=sensor_data.get('soil_moisture'),
            light_intensity=sensor_data.get('light_intensity'),
            co2_concentration=sensor_data.get('co2_concentration')
        )
        session.add(new_sensor_data)
        session.commit()
        
        # 检查阈值并触发警报
        try:
            # 使用线程异步检查，避免阻塞响应
            threading.Thread(
                target=monitor_service.check_thresholds,
                daemon=True
            ).start()
        except Exception as check_err:
            logger.error(f"启动阈值检查失败: {str(check_err)}")
            
        response = jsonify({'data': sensor_data})
        return response
    except Exception as e:
        logger.error(f"获取实时传感器数据失败: {str(e)}")
        session.rollback()
        return jsonify({'error': f'获取实时传感器数据失败: {str(e)}'}), 500
    finally:
        session.close()

# 处理CORS预检请求
@app.route('/sensor-data', methods=['OPTIONS'])
def sensor_data_options():
    """处理传感器数据的预检请求"""
    return '', 204

# 添加与前端匹配的API路由
@app.route('/api/sensor-data')
def api_sensor_data():
    """从虚拟平台获取传感器数据，API路由"""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 确保连接到WSN
        if not device_manager.wsn_client.connected:
            device_manager.connect()
        
        # 从虚拟平台获取数据
        sensor_data = device_manager.get_sensor_data()
        
        if not sensor_data:
            logger.warning("无法从虚拟平台获取传感器数据")
            # 尝试从数据库获取最新数据作为备用
            latest_data = session.query(SensorData).order_by(SensorData.timestamp.desc()).first()
            if latest_data:
                result = latest_data.to_dict()
                return jsonify({'data': result, 'source': 'database'})
            else:
                return jsonify({'error': '无法获取传感器数据'}), 500
            
        # 只在DEBUG级别输出详细数据
        if logger.getEffectiveLevel() <= logging.DEBUG:
            logger.debug(f"API返回传感器数据: {json.dumps(sensor_data, ensure_ascii=False)}")
        
        # 存入数据库
        try:
            new_sensor_data = SensorData(
                air_temperature=sensor_data.get('air_temperature'),
                air_humidity=sensor_data.get('air_humidity'),
                soil_temperature=sensor_data.get('soil_temperature'),
                soil_moisture=sensor_data.get('soil_moisture'),
                light_intensity=sensor_data.get('light_intensity'),
                co2_concentration=sensor_data.get('co2_concentration')
            )
            session.add(new_sensor_data)
            session.commit()
            
            # 检查阈值并触发警报 - 使用线程异步检查，避免阻塞响应
            threading.Thread(
                target=monitor_service.check_thresholds,
                daemon=True
            ).start()
        except Exception as db_error:
            logger.error(f"存储传感器数据失败: {str(db_error)}")
            session.rollback()
            # 即使存储失败，仍然返回获取的数据
            
        response = jsonify({'data': sensor_data, 'source': 'realtime'})
        return response
    except Exception as e:
        logger.error(f"获取传感器数据失败: {str(e)}")
        session.rollback()
        return jsonify({'error': '获取传感器数据失败', 'message': str(e)}), 500
    finally:
        session.close()

@app.route('/api/sensor-data', methods=['OPTIONS'])
def api_sensor_data_options():
    """处理API传感器数据的预检请求"""
    return '', 204

# 添加新的路由来获取设备连接状态
@app.route('/api/device/connection-status')
def get_device_connection_status():
    """获取设备连接状态"""
    try:
        # 修改连接状态判断逻辑：
        # 1. 如果WSN客户端标记为已连接，则认为已连接
        # 2. 如果最近有成功获取传感器数据，也认为已连接
        is_connected = device_manager.wsn_client.connected
        
        # 检查是否有最近的通信记录
        has_recent_communication = False
        if device_manager.wsn_client.last_communication_time:
            try:
                from datetime import datetime
                last_comm_time_str = device_manager.wsn_client.last_communication_time
                last_comm_dt = datetime.fromisoformat(last_comm_time_str)
                current_time = datetime.now()
                # 如果最近30秒内有通信，认为是已连接的
                if (current_time - last_comm_dt).total_seconds() < 30:
                    has_recent_communication = True
                    is_connected = True  # 强制设置为已连接
            except Exception as e:
                logger.warning(f"解析最后通信时间失败: {str(e)}")
        
        # 获取设备状态数量
        device_count = len(device_manager.device_status)
        connected_devices = sum(1 for device in device_manager.device_status.values() if device.get('status') is not None)
        
        # 如果有设备状态信息，也认为是已连接的
        if connected_devices > 0:
            is_connected = True
        
        # 构建响应数据
        response_data = {
            'connected': is_connected,
            'total_devices': device_count,
            'connected_devices': connected_devices,
            'last_communication': device_manager.wsn_client.last_communication_time,
            'has_recent_communication': has_recent_communication
        }
        
        # 如果未连接，尝试在后台重新连接
        if not is_connected:
            # 启动一个线程尝试重新连接
            threading.Thread(target=device_manager.connect, daemon=True).start()
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"获取设备连接状态失败: {str(e)}")
        return jsonify({
            'connected': False,
            'error': str(e)
        }), 500

@app.route('/api/export/sensor-data', methods=['GET'])
def export_sensor_data():
    try:
        # 获取请求参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        metric = request.args.get('metric')
        
        logger.info(f"导出传感器数据，参数: start_time={start_time}, end_time={end_time}, metric={metric}")
        
        # 设置默认时间范围
        if not start_time:
            start_time = (datetime.utcnow() - timedelta(days=7)).isoformat()
        if not end_time:
            end_time = datetime.utcnow().isoformat()
            
        logger.debug(f"查询时间范围: {start_time} 至 {end_time}")
        
        # 将ISO格式字符串转换为datetime对象
        try:
            if isinstance(start_time, str):
                # 尝试解析ISO格式
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                # 尝试解析ISO格式
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError as e:
            logger.error(f"日期解析错误: {e}")
            # 如果解析失败，使用默认时间范围
            start_time = datetime.utcnow() - timedelta(days=7)
            end_time = datetime.utcnow()
            
        logger.debug(f"解析后的时间范围: {start_time} 至 {end_time}")
        
        # 查询数据库
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            query = session.query(SensorData).filter(
                SensorData.timestamp.between(start_time, end_time)
            ).order_by(SensorData.timestamp.desc())
            
            results = query.all()
            logger.info(f"查询到 {len(results)} 条数据记录用于导出")
            
            # 转换为CSV数据
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入CSV头部 - 包含原始字段和兼容字段
            writer.writerow([
                '时间戳', 
                '空气温度(°C)', 
                '空气湿度(%)', 
                '土壤温度(°C)', 
                '土壤湿度(%)', 
                '光照强度(lux)', 
                'CO2浓度(ppm)'
            ])
            
            # 写入数据行
            for record in results:
                # 格式化日期时间为本地时间
                formatted_time = record.timestamp.strftime('%Y-%m-%d %H:%M:%S') if record.timestamp else ''
                
                # 格式化数值，保留1位小数
                air_temp = f"{record.air_temperature:.1f}" if record.air_temperature is not None else ''
                air_hum = f"{record.air_humidity:.1f}" if record.air_humidity is not None else ''
                soil_temp = f"{record.soil_temperature:.1f}" if record.soil_temperature is not None else ''
                soil_moist = f"{record.soil_moisture:.1f}" if record.soil_moisture is not None else ''
                light = f"{int(record.light_intensity)}" if record.light_intensity is not None else ''
                co2 = f"{int(record.co2_concentration)}" if record.co2_concentration is not None else ''
                
                writer.writerow([
                    formatted_time,
                    air_temp,
                    air_hum,
                    soil_temp,
                    soil_moist,
                    light,
                    co2
                ])
            
            # 创建响应
            response = make_response(output.getvalue())
            response.headers["Content-Disposition"] = f"attachment; filename=sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            response.headers["Content-type"] = "text/csv; charset=utf-8"
            
            return response
        finally:
            session.close()
    except Exception as e:
        logger.error(f"导出传感器数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/sensor-data', methods=['OPTIONS'])
def export_sensor_data_options():
    """处理导出数据的预检请求"""
    return '', 204

# 添加历史传感器数据接口，支持分页
@app.route('/api/history/sensor-data', methods=['GET'])
def get_history_sensor_data():
    """获取历史传感器数据，支持分页和时间范围过滤"""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 获取请求参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        metric = request.args.get('metric')  # 可选参数，用于过滤特定指标
        
        # 构建查询
        query = session.query(SensorData)
        
        # 时间范围过滤
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                query = query.filter(SensorData.timestamp >= start_dt)
            except (ValueError, TypeError) as e:
                logger.warning(f"无效的开始时间格式: {start_time}, 错误: {str(e)}")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                query = query.filter(SensorData.timestamp <= end_dt)
            except (ValueError, TypeError) as e:
                logger.warning(f"无效的结束时间格式: {end_time}, 错误: {str(e)}")
        
        # 按时间倒序排序
        query = query.order_by(SensorData.timestamp.desc())
        
        # 计算总记录数
        total_count = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 执行查询
        results = query.all()
        
        # 转换为字典列表
        data = [item.to_dict() for item in results]
        
        # 返回带有分页信息的响应
        response_data = {
            'data': {
                'items': data,
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'pages': (total_count + page_size - 1) // page_size  # 计算总页数
            }
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"获取历史传感器数据失败: {str(e)}")
        session.rollback()
        return jsonify({'error': '获取历史传感器数据失败', 'message': str(e)}), 500
    finally:
        session.close()

@app.route('/api/history/sensor-data', methods=['OPTIONS'])
def history_sensor_data_options():
    """处理历史传感器数据的预检请求"""
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)