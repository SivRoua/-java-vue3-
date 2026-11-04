from flask import Blueprint, request, jsonify
from device.auto_control import AutoControlManager
import logging

auto_control_bp = Blueprint('auto_control', __name__)
logger = logging.getLogger(__name__)

# 自动控制管理器实例将在app.py中初始化并注入
auto_control_manager = None

def init_auto_control_manager(manager):
    """初始化自动控制管理器"""
    global auto_control_manager
    auto_control_manager = manager
    logger.info("自动控制管理器已初始化")

@auto_control_bp.route('/status', methods=['GET'])
def get_auto_control_status():
    """获取自动控制状态"""
    if not auto_control_manager:
        return jsonify({'error': '自动控制管理器未初始化'}), 500
    
    try:
        # 获取当前自动控制状态
        is_enabled = auto_control_manager.is_enabled()
        thresholds = auto_control_manager.get_thresholds()
        
        return jsonify({
            'enabled': is_enabled,
            'thresholds': {k: {'min': v[0], 'max': v[1]} for k, v in thresholds.items()},
            'message': '自动控制' + ('已启用' if is_enabled else '未启用')
        })
    except Exception as e:
        logger.error(f"获取自动控制状态失败: {str(e)}")
        return jsonify({'error': f'获取自动控制状态失败: {str(e)}'}), 500@auto_control_bp.route('/enable', methods=['POST'])
def enable_auto_control():
    """启用自动控制"""
    if not auto_control_manager:
        return jsonify({'error': '自动控制管理器未初始化'}), 500
    
    try:
        # 启动自动控制
        success = auto_control_manager.start_auto_control()
        
        if success:
            return jsonify({
                'message': '自动控制已启用',
                'enabled': True
            })
        else:
            return jsonify({
                'error': '启用自动控制失败',
                'enabled': False
            }), 500
    except Exception as e:
        logger.error(f"启用自动控制失败: {str(e)}")
        return jsonify({'error': f'启用自动控制失败: {str(e)}'}), 500

@auto_control_bp.route('/disable', methods=['POST'])
def disable_auto_control():
    """禁用自动控制"""
    if not auto_control_manager:
        return jsonify({'error': '自动控制管理器未初始化'}), 500
    
    try:
        # 停止自动控制
        success = auto_control_manager.stop_auto_control()
        
        if success:
            return jsonify({
                'message': '自动控制已禁用',
                'enabled': False
            })
        else:
            return jsonify({
                'error': '禁用自动控制失败',
                'enabled': True
            }), 500
    except Exception as e:
        logger.error(f"禁用自动控制失败: {str(e)}")
        return jsonify({'error': f'禁用自动控制失败: {str(e)}'}), 500@auto_control_bp.route('/thresholds', methods=['GET'])
def get_thresholds():
    """获取阈值设置"""
    if not auto_control_manager:
        return jsonify({'error': '自动控制管理器未初始化'}), 500
    
    try:
        # 获取当前阈值设置
        thresholds = auto_control_manager.get_thresholds()
        
        # 转换为前端友好格式
        formatted_thresholds = {}
        for sensor_type, (min_val, max_val) in thresholds.items():
            formatted_thresholds[sensor_type] = {
                'min': min_val,
                'max': max_val
            }
        
        return jsonify(formatted_thresholds)
    except Exception as e:
        logger.error(f"获取阈值设置失败: {str(e)}")
        return jsonify({'error': f'获取阈值设置失败: {str(e)}'}), 500

@auto_control_bp.route('/thresholds', methods=['POST'])
def update_thresholds():
    """更新阈值设置"""
    if not auto_control_manager:
        return jsonify({'error': '自动控制管理器未初始化'}), 500
    
    try:
        # 从请求中获取新的阈值设置
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        # 转换为内部格式
        new_thresholds = {}
        for sensor_type, threshold in data.items():
            if isinstance(threshold, dict) and 'min' in threshold and 'max' in threshold:
                new_thresholds[sensor_type] = (threshold['min'], threshold['max'])
            else:
                logger.warning(f"无效的阈值格式: {sensor_type} {threshold}")
        
        if not new_thresholds:
            return jsonify({'error': '无有效阈值数据'}), 400
        
        # 更新阈值
        success = auto_control_manager.update_thresholds(new_thresholds)
        
        if success:
            return jsonify({
                'message': '阈值设置已更新',
                'thresholds': {k: {'min': v[0], 'max': v[1]} for k, v in auto_control_manager.get_thresholds().items()}
            })
        else:
            return jsonify({
                'error': '更新阈值设置失败',
                'thresholds': {k: {'min': v[0], 'max': v[1]} for k, v in auto_control_manager.get_thresholds().items()}
            }), 500
    except Exception as e:
        logger.error(f"更新阈值设置失败: {str(e)}")
        return jsonify({'error': f'更新阈值设置失败: {str(e)}'}), 500