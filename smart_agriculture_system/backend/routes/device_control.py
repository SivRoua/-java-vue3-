from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from device.device_manager import DeviceManager
from models.device_status import DeviceStatus
from models.operation_log import OperationLog
from models.sensor_data import SensorData
from config.database import Config
import logging
import datetime

device_bp = Blueprint('device', __name__)
logger = logging.getLogger(__name__)

# 创建数据库会话
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

device_manager = DeviceManager()

@device_bp.route('/devices', methods=['GET'])
def get_devices():
    """获取所有设备列表，无需JWT认证"""
    try:
        # 从配置中获取设备列表
        from config.hardware_config import DEVICE_CONFIG
        
        devices = []
        for device_type, config in DEVICE_CONFIG.items():
            devices.append({
                'type': device_type,
                'name': config.get('name', device_type),
                'description': config.get('description', '')
            })
            
        return jsonify(devices)
    except Exception as e:
        logger.error(f"获取设备列表失败: {str(e)}")
        return jsonify({'error': '获取设备列表失败'}), 500

@device_bp.route('/control', methods=['POST'])
def control_device():
    """控制设备，无需JWT认证"""
    session = Session()
    try:
        # 打印请求数据以便调试
        logger.info(f"收到控制请求: {request.data}")
        
        # 尝试解析JSON数据
        try:
            data = request.get_json(force=True)
        except Exception as e:
            logger.error(f"解析JSON数据失败: {str(e)}")
            return jsonify({'error': f'无效的请求数据格式: {str(e)}'}), 400
            
        logger.info(f"解析后的请求数据: {data}")
        
        device_type = data.get('device_type')
        action = data.get('action')
        
        if not device_type or not action:
            return jsonify({'error': '设备类型和操作不能为空'}), 400
            
        if action not in ['open', 'close']:
            return jsonify({'error': f'无效的操作类型: {action}，必须是 open 或 close'}), 400
        
        # 从配置中获取设备信息
        from config.hardware_config import DEVICE_CONFIG
        device_config = DEVICE_CONFIG.get(device_type)
        if not device_config:
            return jsonify({'error': f'未知的设备类型: {device_type}'}), 400
            
        device_name = device_config.get('name', device_type)
        
        # 确保设备连接
        if not device_manager.wsn_client.connected:
            logger.info("设备未连接，尝试连接...")
            connect_result = device_manager.connect()
            if not connect_result:
                logger.error("无法连接到设备控制器")
                return jsonify({
                    'error': '无法连接到设备控制器',
                    'message': '请检查虚拟平台是否正常运行'
                }), 500
            logger.info("成功连接到设备控制器")
            
        # 执行设备控制
        logger.info(f"执行设备控制: {device_name}({device_type}) {action}")
        success = device_manager.control_device(device_type, action)
        
        # 更新设备状态
        device_status = session.query(DeviceStatus).filter_by(device_type=device_type).first()
        if device_status:
            device_status.status = 1 if action == 'open' else 0
        else:
            # 如果设备状态记录不存在，创建一个新记录
            device_status = DeviceStatus(
                device_type=device_type,
                status=1 if action == 'open' else 0
            )
            session.add(device_status)
            
        # 记录操作日志
        log = OperationLog(
            user_id=0,  # 匿名用户
            operation_type=action,
            device_type=device_type,
            operation_result=success,
            description=f"执行了{device_name}({device_type})的{action}操作"
        )
        session.add(log)
        session.commit()
        
        if success:
            # 获取更新后的设备状态
            updated_status = device_manager.get_device_status(device_type)
            return jsonify({
                'message': f'设备 {device_type} {action} 操作成功',
                'status': updated_status,
                'success': True
            })
        return jsonify({
            'error': '设备控制失败',
            'message': f'设备 {device_type} {action} 操作失败',
            'success': False
        }), 500
        
    except Exception as e:
        logger.error(f"设备控制错误: {str(e)}")
        session.rollback()
        return jsonify({
            'error': f'设备控制出错: {str(e)}',
            'message': '请检查设备连接状态',
            'success': False
        }), 500
    finally:
        session.close()

@device_bp.route('/status', methods=['GET'])
def get_device_status():
    """获取设备状态，无需JWT认证"""
    session = Session()
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
    finally:
        session.close()

@device_bp.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    """获取传感器数据，无需JWT认证"""
    session = Session()
    try:
        # 获取最新的传感器数据
        latest_data = session.query(SensorData).order_by(SensorData.timestamp.desc()).first()
        if not latest_data:
            return jsonify({'error': '没有可用的传感器数据'}), 404
        return jsonify(latest_data.to_dict())
    except Exception as e:
        logger.error(f"获取传感器数据失败: {str(e)}")
        return jsonify({'error': '获取传感器数据失败'}), 500
    finally:
        session.close()

@device_bp.route('/realtime-sensor-data', methods=['GET'])
def get_realtime_sensor_data():
    """获取实时传感器数据，优化连接失败处理"""
    return get_public_sensor_data()  # 复用相同的实现逻辑

# 不需要JWT的端点，用于直接获取传感器数据
@device_bp.route('/public/sensor-data', methods=['GET'])
def get_public_sensor_data():
    """公开的接口，获取传感器数据，即使连接失败也返回最新数据"""
    session = Session()
    try:
        # 首先尝试获取实时数据
        realtime_data = None
        connection_error = None
        
        # 尝试连接并获取实时数据，但不阻断流程
        try:
            # 检查连接状态
            if not device_manager.wsn_client.connected:
                logger.info("设备未连接，尝试连接...")
                device_manager.connect()
            
            # 如果连接成功，获取实时数据
            if device_manager.wsn_client.connected:
                realtime_data = device_manager.get_sensor_data()
                if realtime_data:
                    logger.info("成功获取实时传感器数据")
                    
                    # 存入数据库
                    new_sensor_data = SensorData(
                        air_temperature=realtime_data.get('air_temperature'),
                        air_humidity=realtime_data.get('air_humidity'),
                        soil_temperature=realtime_data.get('soil_temperature'),
                        soil_moisture=realtime_data.get('soil_moisture'),
                        light_intensity=realtime_data.get('light_intensity'),
                        co2_concentration=realtime_data.get('co2_concentration')
                    )
                    session.add(new_sensor_data)
                    session.commit()
                    logger.info("成功将传感器数据存入数据库")
        except Exception as e:
            connection_error = str(e)
            logger.warning(f"获取实时传感器数据失败: {str(e)}，将尝试返回数据库中的最新数据")
            session.rollback()  # 回滚任何未完成的事务
        
        # 如果无法获取实时数据，则从数据库获取最新数据
        if not realtime_data:
            try:
                latest_data = session.query(SensorData).order_by(SensorData.timestamp.desc()).first()
                if latest_data:
                    logger.info("从数据库获取最新传感器数据")
                    result = {
                        'data': latest_data.to_dict(),
                        'source': 'database',
                        'timestamp': latest_data.timestamp.isoformat() if hasattr(latest_data.timestamp, 'isoformat') else str(latest_data.timestamp)
                    }
                    
                    # 如果有连接错误，添加到响应中
                    if connection_error:
                        result['connection_error'] = connection_error
                        
                    return jsonify(result)
                else:
                    # 如果数据库也没有数据，返回默认值
                    logger.warning("数据库中没有传感器数据，返回默认值")
                    default_data = {
                        'air_temperature': 0.0,
                        'air_humidity': 0.0,
                        'soil_temperature': 0.0,
                        'soil_moisture': 0.0,
                        'light_intensity': 0.0,
                        'co2_concentration': 0.0
                    }
                    
                    result = {
                        'data': default_data,
                        'source': 'default',
                        'connection_error': connection_error or '无可用数据'
                    }
                    
                    return jsonify(result)
            except Exception as db_error:
                logger.error(f"从数据库获取传感器数据失败: {str(db_error)}")
                return jsonify({
                    'error': f'获取传感器数据失败: {str(db_error)}',
                    'connection_error': connection_error
                }), 500
        
        # 如果成功获取了实时数据，直接返回
        return jsonify({
            'data': realtime_data,
            'source': 'realtime',
            'timestamp': datetime.datetime.now().isoformat()
        })
            
    except Exception as e:
        logger.error(f"处理传感器数据请求失败: {str(e)}")
        session.rollback()
        return jsonify({'error': f'处理传感器数据请求失败: {str(e)}'}), 500
    finally:
        session.close()

@device_bp.route('/connect', methods=['POST'])
def connect_device():
    """连接设备"""
    try:
        # 尝试连接设备
        result = device_manager.connect()
        
        if result:
            return jsonify({
                'status': 'connected',
                'message': '设备连接成功',
                'connected': True
            })
        else:
            return jsonify({
                'status': 'disconnected',
                'message': '设备连接失败',
                'connected': False
            }), 500
    except Exception as e:
        logger.error(f"连接设备失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'连接设备时出错: {str(e)}',
            'connected': False
        }), 500

@device_bp.route('/disconnect', methods=['POST'])
def disconnect_device():
    """获取连接状态（不再实际断开，后端自动管理连接）"""
    # 这个方法实际上并不会断开连接，因为我们希望后端保持连接
    # 只是返回当前连接状态
    try:
        is_connected = device_manager.wsn_client.connected
        
        return jsonify({
            'status': 'connected' if is_connected else 'disconnected',
            'message': '设备保持连接状态，后端自动管理连接'
        })
            
    except Exception as e:
        logger.error(f"检查设备连接状态出错: {str(e)}")
        return jsonify({'error': f'检查设备连接状态出错: {str(e)}'}), 500

@device_bp.route('/connection-status', methods=['GET'])
def get_connection_status():
    """获取设备连接状态"""
    try:
        # 检查连接状态
        if not device_manager.wsn_client.connected:
            try:
                logger.info("设备未连接，尝试连接...")
                device_manager.connect()
            except Exception as e:
                logger.error(f"尝试连接设备失败: {str(e)}")
        
        # 获取连接状态信息
        is_connected = device_manager.wsn_client.connected
        last_connection = device_manager.wsn_client.last_connection_time
        last_communication = device_manager.wsn_client.last_communication_time
        
        # 获取设备数量信息
        total_devices = len(device_manager.device_status)
        connected_devices = sum(1 for device in device_manager.device_status.values() if device.get('status') is not None)
        
        # 构建响应
        response = {
            'status': 'connected' if is_connected else 'disconnected',
            'message': '已连接' if is_connected else '未连接',
            'connected': is_connected,
            'last_connection': last_connection,
            'last_communication': last_communication,
            'total_devices': total_devices,
            'connected_devices': connected_devices if is_connected else 0
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"获取连接状态失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取连接状态时出错: {str(e)}',
            'connected': False,
            'total_devices': len(device_manager.device_status),
            'connected_devices': 0
        }), 500