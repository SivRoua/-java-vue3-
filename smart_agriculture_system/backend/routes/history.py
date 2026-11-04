from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, verify_jwt_in_request, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.sensor_data import SensorData
from config.database import Config
import logging
import traceback

# 配置日志
logger = logging.getLogger(__name__)

history_bp = Blueprint('history', __name__)
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

@history_bp.route('/data', methods=['GET'])
def get_history_data():
    # 尝试验证 token，但不强制要求（如果 token 无效或不存在，继续处理请求）
    try:
        # 检查是否有 Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header and auth_header.startswith('Bearer '):
            # 如果有 token，尝试验证
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                if user_id:
                    logger.debug(f"已验证用户身份: {user_id}")
            except Exception as jwt_error:
                # Token 无效，但不影响数据访问，记录日志并继续
                logger.debug(f"Token验证失败，继续处理请求: {str(jwt_error)}")
    except Exception as e:
        # 任何其他错误都不影响数据访问
        logger.debug(f"Token处理异常，继续处理请求: {str(e)}")
    session = None
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        logger.info(f"获取历史数据，参数: start_date={start_date}, end_date={end_date}")
        
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
            
        logger.debug(f"查询时间范围: {start_date} 至 {end_date}")
        
        # 将ISO格式字符串转换为datetime对象
        try:
            if isinstance(start_date, str):
                # 尝试解析ISO格式
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                # 尝试解析ISO格式
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError as e:
            logger.error(f"日期解析错误: {e}")
            # 如果解析失败，使用默认时间范围
            start_date = datetime.utcnow() - timedelta(days=1)
            end_date = datetime.utcnow()
            
        logger.debug(f"解析后的时间范围: {start_date} 至 {end_date}")
            
        session = Session()
        query = session.query(SensorData).filter(
            SensorData.timestamp.between(start_date, end_date)
        )
        
        results = query.all()
        logger.info(f"查询到 {len(results)} 条数据记录")
        
        # 转换为字典列表并使用to_dict方法
        data = []
        for record in results:
            try:
                # 使用模型的to_dict方法
                record_dict = record.to_dict()
                data.append(record_dict)
            except Exception as e:
                logger.error(f"转换记录失败: {str(e)}")
                logger.error(traceback.format_exc())
        
        return jsonify(data)
    except Exception as e:
        logger.error(f"获取历史数据失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@history_bp.route('', methods=['GET'])
def get_history_data_compat():
    """兼容前端直接请求 /api/history 的路由"""
    return get_history_data()

@history_bp.route('/data', methods=['OPTIONS'])
def history_data_options():
    """处理历史数据的预检请求"""
    return '', 204

@history_bp.route('', methods=['OPTIONS'])
def history_options():
    """处理历史数据根路径的预检请求"""
    return '', 204

@history_bp.route('/summary', methods=['GET'])
def get_summary():
    # 尝试验证 token，但不强制要求
    try:
        auth_header = request.headers.get('Authorization', '')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                if user_id:
                    logger.debug(f"已验证用户身份: {user_id}")
            except Exception as jwt_error:
                logger.debug(f"Token验证失败，继续处理请求: {str(jwt_error)}")
    except Exception as e:
        logger.debug(f"Token处理异常，继续处理请求: {str(e)}")
    session = None
    try:
        session = Session()
        last_record = session.query(SensorData).order_by(
            SensorData.timestamp.desc()
        ).first()
        
        if not last_record:
            logger.warning("没有找到历史数据")
            return jsonify({'error': '没有历史数据'}), 404
        
        # 使用安全的方式构建记录字典
        result = {
            'id': last_record.id,
            'timestamp': last_record.timestamp.isoformat() if last_record.timestamp else None,
            'air_temperature': last_record.air_temperature,
            'air_humidity': last_record.air_humidity,
            'soil_temperature': last_record.soil_temperature,
            'soil_moisture': last_record.soil_moisture,
            'light_intensity': last_record.light_intensity,
        }
        
        # 安全地添加co2_concentration字段
        try:
            result['co2_concentration'] = last_record.co2_concentration
        except:
            result['co2_concentration'] = None
            
        logger.info(f"返回最新数据记录: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取数据摘要失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@history_bp.route('/sensor-data', methods=['GET'])
def get_sensor_history_data():
    # 尝试验证 token，但不强制要求
    try:
        auth_header = request.headers.get('Authorization', '')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                if user_id:
                    logger.debug(f"已验证用户身份: {user_id}")
            except Exception as jwt_error:
                logger.debug(f"Token验证失败，继续处理请求: {str(jwt_error)}")
    except Exception as e:
        logger.debug(f"Token处理异常，继续处理请求: {str(e)}")
    session = None
    try:
        # 获取请求参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        metric = request.args.get('metric')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        logger.info(f"获取历史传感器数据，参数: start_time={start_time}, end_time={end_time}, metric={metric}, page={page}, page_size={page_size}")
        
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
        session = Session()
        query = session.query(SensorData).filter(
            SensorData.timestamp.between(start_time, end_time)
        ).order_by(SensorData.timestamp.desc())
        
        # 计算总记录数
        total_count = query.count()
        
        # 分页
        results = query.limit(page_size).offset((page - 1) * page_size).all()
        logger.info(f"查询到 {len(results)} 条数据记录，总记录数: {total_count}")
        
        # 转换为字典列表
        data = []
        for record in results:
            try:
                # 使用模型的to_dict方法
                record_dict = record.to_dict()
                
                # 添加兼容性字段
                record_dict['temperature'] = record_dict.get('air_temperature')
                record_dict['humidity'] = record_dict.get('air_humidity')
                record_dict['co2_level'] = record_dict.get('co2_concentration')
                
                data.append(record_dict)
            except Exception as e:
                logger.error(f"转换记录失败: {str(e)}")
                logger.error(traceback.format_exc())
        
        # 构建响应
        response = {
            'data': data,
            'meta': {
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'pages': (total_count + page_size - 1) // page_size
            }
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"获取历史传感器数据失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@history_bp.route('/sensor-data', methods=['OPTIONS'])
def sensor_data_options():
    """处理历史传感器数据的预检请求"""
    return '', 204