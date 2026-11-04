from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
import jwt
from models.user import User
from config.settings import JWT_SECRET_KEY
import logging
import traceback

logger = logging.getLogger(__name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # 使用 flask_jwt_extended 验证 token
            verify_jwt_in_request()
            claims = get_jwt()
            
            # 获取用户信息
            user_id = claims.get('user_id')
            if not user_id:
                logger.error("Token中缺少user_id字段")
                response = jsonify({'message': 'Invalid token, missing user_id'})
                response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', 'http://localhost:3000'))
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
                response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response, 401
                
            # 使用db.session直接查询
            from extensions import db
            current_user = db.session.query(User).filter(User.id == user_id).first()
            
            if not current_user:
                logger.error(f"未找到用户ID: {user_id}")
                response = jsonify({'message': 'User not found'})
                response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', 'http://localhost:3000'))
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
                response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response, 401
                
            # 将用户对象添加到请求中
            request.user = current_user
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Token验证失败: {str(e)}")
            logger.error(traceback.format_exc())
            response = jsonify({'message': str(e)})
            response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', 'http://localhost:3000'))
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response, 401
        
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # 确保已经通过了token_required装饰器
            if not hasattr(request, 'user'):
                logger.error("缺少用户认证")
                response = jsonify({'message': 'Authentication required'})
                response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', 'http://localhost:3000'))
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
                response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response, 401
                
            # 检查用户是否是管理员
            if request.user.role != 'admin':
                logger.error(f"用户 {request.user.username} 不是管理员，无法访问")
                response = jsonify({'message': 'Admin privileges required'})
                response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', 'http://localhost:3000'))
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
                response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response, 403
                
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"管理员权限验证失败: {str(e)}")
            logger.error(traceback.format_exc())
            response = jsonify({'message': str(e)})
            response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', 'http://localhost:3000'))
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response, 403
        
    return decorated 