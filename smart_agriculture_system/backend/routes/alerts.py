from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models.operation_log import OperationLog
from models.threshold_settings import ThresholdSetting
from config.database import Config
import logging
import datetime

alerts_bp = Blueprint('alerts', __name__)
logger = logging.getLogger(__name__)

# 创建数据库会话
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

@alerts_bp.route('/recent', methods=['GET'])
def get_recent_alerts():
    """获取最近的警报，无需JWT认证"""
    session = Session()
    try:
        # 获取请求参数
        limit = request.args.get('limit', 5, type=int)
        
        # 从操作日志中获取警报记录
        alerts = []
        logs = session.query(OperationLog).order_by(
            desc(OperationLog.operation_time)
        ).limit(limit).all()
        
        for log in logs:
            # 根据操作类型判断是否为警报
            if 'error' in log.operation_type.lower() or not log.operation_result:
                status = '未处理'
            else:
                status = '已处理'
                
            alerts.append({
                'id': log.id,
                'time': log.operation_time.isoformat() if log.operation_time else None,
                'type': log.operation_type,
                'description': log.description,
                'status': status
            })
            
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"获取最近警报失败: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@alerts_bp.route('/handle/<int:alert_id>', methods=['PUT'])
@jwt_required(optional=True)
def handle_alert(alert_id):
    """标记警报为已处理"""
    session = Session()
    try:
        # 查找操作日志
        log = session.query(OperationLog).filter_by(id=alert_id).first()
        
        if not log:
            return jsonify({'error': '未找到警报记录'}), 404
        
        # 更新为已处理状态
        log.operation_result = True
        session.commit()
        
        return jsonify({
            'id': log.id,
            'status': '已处理',
            'message': '警报已标记为已处理'
        })
    except Exception as e:
        session.rollback()
        logger.error(f"标记警报为已处理失败: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@alerts_bp.route('/count', methods=['GET'])
def get_alert_count():
    """获取未处理警报数量，无需JWT认证"""
    session = Session()
    try:
        # 获取未处理警报数量
        count = session.query(OperationLog).filter(
            OperationLog.operation_result == False
        ).count()
        
        return jsonify({'count': count})
    except Exception as e:
        logger.error(f"获取警报数量失败: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@alerts_bp.route('/rules', methods=['GET'])
@jwt_required(optional=True)
def get_alert_rules():
    """获取所有警报规则"""
    session = Session()
    try:
        rules = session.query(ThresholdSetting).all()
        result = [rule.to_dict() for rule in rules]
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取警报规则失败: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@alerts_bp.route('/rules/<int:rule_id>', methods=['GET'])
@jwt_required(optional=True)
def get_alert_rule(rule_id):
    """获取单个警报规则"""
    session = Session()
    try:
        rule = session.query(ThresholdSetting).filter_by(id=rule_id).first()
        if not rule:
            return jsonify({'error': '未找到警报规则'}), 404
        return jsonify(rule.to_dict())
    except Exception as e:
        logger.error(f"获取警报规则失败: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@alerts_bp.route('/rules', methods=['POST'])
@jwt_required()
def create_alert_rule():
    """创建警报规则"""
    session = Session()
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '未收到有效的请求数据'}), 400
            
        user_id = get_jwt_identity()
        
        # 验证必填字段
        required_fields = ['name', 'type', 'operator', 'threshold']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 验证数值类型
        try:
            threshold = float(data['threshold'])
        except (ValueError, TypeError):
            return jsonify({'error': '阈值必须为数值类型'}), 400
        
        # 验证操作符
        if data['operator'] not in ['>', '<', '>=', '<=', '==']:
            return jsonify({'error': '无效的操作符，支持的操作符: >, <, >=, <=, =='}), 400
            
        # 验证监测类型
        valid_types = ['temperature', 'humidity', 'soil_moisture', 'soil_temperature', 'light_intensity', 'co2_level']
        if data['type'] not in valid_types:
            return jsonify({'error': f'无效的监测类型，支持的类型: {", ".join(valid_types)}'}), 400
        
        # 创建新规则
        new_rule = ThresholdSetting(
            name=data['name'],
            type=data['type'],
            operator=data['operator'],
            threshold=threshold,
            enabled=data.get('enabled', True),
            user_id=user_id
        )
        
        session.add(new_rule)
        session.commit()
        
        # 返回完整的规则数据，包括ID
        return jsonify(new_rule.to_dict()), 201
    except Exception as e:
        session.rollback()
        logger.error(f"创建警报规则失败: {str(e)}")
        return jsonify({'error': f'创建警报规则失败: {str(e)}'}), 500
    finally:
        session.close()

@alerts_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@jwt_required()
def update_alert_rule(rule_id):
    """更新警报规则"""
    session = Session()
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '未收到有效的请求数据'}), 400
            
        rule = session.query(ThresholdSetting).filter_by(id=rule_id).first()
        
        if not rule:
            return jsonify({'error': '未找到警报规则'}), 404
        
        # 更新字段，进行数据验证
        if 'name' in data:
            rule.name = data['name']
            
        if 'type' in data:
            # 验证监测类型
            valid_types = ['temperature', 'humidity', 'soil_moisture', 'soil_temperature', 'light_intensity', 'co2_level']
            if data['type'] not in valid_types:
                return jsonify({'error': f'无效的监测类型，支持的类型: {", ".join(valid_types)}'}), 400
            rule.type = data['type']
            
        if 'operator' in data:
            # 验证操作符
            if data['operator'] not in ['>', '<', '>=', '<=', '==']:
                return jsonify({'error': '无效的操作符，支持的操作符: >, <, >=, <=, =='}), 400
            rule.operator = data['operator']
            
        if 'threshold' in data:
            # 验证数值类型
            try:
                rule.threshold = float(data['threshold'])
            except (ValueError, TypeError):
                return jsonify({'error': '阈值必须为数值类型'}), 400
                
        if 'enabled' in data:
            rule.enabled = bool(data['enabled'])
        
        rule.update_time = datetime.datetime.utcnow()
        session.commit()
        
        return jsonify(rule.to_dict())
    except Exception as e:
        session.rollback()
        logger.error(f"更新警报规则失败: {str(e)}")
        return jsonify({'error': f'更新警报规则失败: {str(e)}'}), 500
    finally:
        session.close()

@alerts_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_alert_rule(rule_id):
    """删除警报规则"""
    session = Session()
    try:
        rule = session.query(ThresholdSetting).filter_by(id=rule_id).first()
        
        if not rule:
            return jsonify({'error': '未找到警报规则'}), 404
        
        session.delete(rule)
        session.commit()
        
        return jsonify({'message': '删除成功'})
    except Exception as e:
        session.rollback()
        logger.error(f"删除警报规则失败: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@alerts_bp.route('/rules/<int:rule_id>/toggle', methods=['PUT'])
@jwt_required()
def toggle_alert_rule(rule_id):
    """切换警报规则启用状态"""
    session = Session()
    try:
        rule = session.query(ThresholdSetting).filter_by(id=rule_id).first()
        
        if not rule:
            return jsonify({'error': '未找到警报规则'}), 404
        
        # 切换启用状态
        rule.enabled = not rule.enabled
        rule.update_time = datetime.datetime.utcnow()
        
        try:
            session.commit()
            logger.info(f"已切换警报规则 {rule_id} 的状态为 {'启用' if rule.enabled else '禁用'}")
        except Exception as commit_error:
            session.rollback()
            logger.error(f"提交数据库更新失败: {str(commit_error)}")
            return jsonify({'error': f'更新数据库失败: {str(commit_error)}'}), 500
        
        return jsonify({
            'id': rule.id,
            'enabled': rule.enabled,
            'message': f'警报规则已{("启用" if rule.enabled else "禁用")}'
        })
    except Exception as e:
        session.rollback()
        logger.error(f"切换警报规则状态失败: {str(e)}")
        return jsonify({'error': f'切换警报规则状态失败: {str(e)}'}), 500
    finally:
        session.close()

@alerts_bp.route('/auto-control/rules', methods=['GET'])
@jwt_required(optional=True)
def get_auto_control_rules():
    """获取所有自动控制规则"""
    try:
        # 从app获取自动控制服务
        from app import auto_control_service
        
        if not auto_control_service:
            return jsonify({'error': '自动控制服务未初始化'}), 500
            
        # 返回控制规则
        rules = []
        for sensor_type, type_rules in auto_control_service.control_rules.items():
            for rule in type_rules:
                operator, threshold, device_type, action = rule
                rules.append({
                    'sensor_type': sensor_type,
                    'operator': operator,
                    'threshold': threshold,
                    'device_type': device_type,
                    'action': action
                })
                
        return jsonify(rules)
    except Exception as e:
        logger.error(f"获取自动控制规则失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/auto-control/logs', methods=['GET'])
@jwt_required(optional=True)
def get_auto_control_logs():
    """获取自动控制操作日志"""
    session = Session()
    try:
        # 获取请求参数
        limit = request.args.get('limit', 10, type=int)
        
        # 从操作日志中获取自动控制记录
        logs = session.query(OperationLog).filter(
            OperationLog.operation_type == "自动控制"
        ).order_by(
            desc(OperationLog.operation_time)
        ).limit(limit).all()
        
        result = []
        for log in logs:
            result.append({
                'id': log.id,
                'time': log.operation_time.isoformat() if log.operation_time else None,
                'device_type': log.device_type,
                'description': log.description,
                'result': log.operation_result
            })
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取自动控制日志失败: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()