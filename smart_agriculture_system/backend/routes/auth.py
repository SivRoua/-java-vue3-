from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from services.auth_service import AuthService
import logging

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        logger.info(f"收到登录请求，数据类型: {type(request.data)}")
        data = request.get_json()
        logger.info(f"解析的JSON数据: {data}")
        
        if not data:
            logger.warning("无效的请求数据")
            return jsonify({'error': '无效的请求数据'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        logger.info(f"提取的登录信息: 用户名={username}, 密码长度={len(password) if password else 0}")
        
        if not username or not password:
            logger.warning("用户名或密码为空")
            return jsonify({'error': '用户名和密码不能为空'}), 400
            
        logger.info(f"尝试登录用户: {username}")
        user_data = auth_service.authenticate_user(username, password)
        
        if not user_data:
            logger.warning(f"登录失败: 用户名或密码错误 - {username}")
            return jsonify({'error': '用户名或密码错误'}), 401
            
        # 创建包含额外信息的token
        token_data = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'role': user_data['role']
        }
        # PyJWT 2.10+ 要求 sub 必须是字符串，因此 identity 转成 str
        access_token = create_access_token(identity=str(user_data['id']), additional_claims=token_data)
        logger.info(f"用户登录成功: {username}")
        logger.info(f"用户信息: {user_data}")
        
        response_data = {
            'access_token': access_token,
            'user': user_data
        }
        logger.info(f"返回响应: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"登录过程中发生错误: {str(e)}")
        return jsonify({'error': '登录过程中发生错误'}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        admin_username = data.get('admin_username')
        admin_password = data.get('admin_password')
        
        if not username or not password or not email or not admin_username or not admin_password:
            return jsonify({'error': '所有字段都不能为空'}), 400
        
        # 验证管理员凭据
        admin_data = auth_service.authenticate_user(admin_username, admin_password)
        
        if not admin_data or admin_data['role'] != 'admin':
            return jsonify({'error': '管理员验证失败，无法注册新用户'}), 401
        
        # 检查用户名是否已存在
        if auth_service.check_username_exists(username):
            return jsonify({'error': '用户名已存在'}), 400
            
        # 检查邮箱是否已存在
        if auth_service.check_email_exists(email):
            return jsonify({'error': '邮箱已存在'}), 400
        
        # 创建新用户
        new_user = auth_service.create_user(username, password, email)
        
        if not new_user:
            return jsonify({'error': '创建用户失败'}), 500
            
        return jsonify({
            'status': 'success',
            'message': '用户注册成功',
            'username': username
        })
        
    except Exception as e:
        logger.error(f"注册过程中发生错误: {str(e)}")
        return jsonify({'error': '注册过程中发生错误'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        user_data = auth_service.get_user_by_id(current_user_id)
        
        if not user_data:
            return jsonify({'error': '用户不存在'}), 404
            
        return jsonify(user_data)
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({'error': '获取用户信息失败'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    try:
        current_user_id = get_jwt_identity()
        user_data = auth_service.get_user_by_id(current_user_id)
        
        if not user_data:
            return jsonify({'error': '用户不存在'}), 404
            
        # 创建新的访问令牌
        access_token = create_access_token(identity=current_user_id)
        logger.info(f"用户令牌刷新成功: {user_data['username']}")
        
        return jsonify({
            'access_token': access_token,
            'user': user_data
        })
        
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}")
        return jsonify({'error': '刷新令牌失败'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    # JWT是无状态的，服务端不需要做任何操作
    # 客户端需要删除token
    return jsonify({'status': 'success', 'message': '登出成功'})