from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from models.user import User
from middleware.auth import admin_required, token_required
from extensions import db
import logging
from datetime import datetime
import traceback
import pymysql

# 配置日志
logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    """获取用户列表"""
    try:
        logger.info("尝试获取用户列表")
        
        # 直接使用db.session查询，避免可能的User.query问题
        users = db.session.query(User).all()
        logger.info(f"查询到 {len(users) if users else 0} 个用户")
        
        user_list = []
        for user in users:
            try:
                logger.debug(f"处理用户数据: id={user.id}, username={user.username}")
                user_dict = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active if user.is_active is not None else True,
                    'role': user.role if user.role is not None else 'user',
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
                user_list.append(user_dict)
            except Exception as e:
                logger.error(f"转换用户数据失败: {str(e)}")
                logger.error(traceback.format_exc())
                continue
                
        logger.info(f"成功获取 {len(user_list)} 个用户")
        
        # 返回成功响应
        response = jsonify({
            'status': 'success',
            'data': user_list
        })
        
        # 添加CORS头，使用特定的域名而不是通配符
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', 'http://localhost:3000'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        
        return response, 200
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        logger.error(traceback.format_exc())
        
        response = jsonify({
            'status': 'error',
            'message': str(e)
        })
        
        # 添加CORS头，使用特定的域名而不是通配符
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', 'http://localhost:3000'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        
        return response, 500

@users_bp.route('/users', methods=['POST'])
@token_required
@admin_required
def create_user():
    """创建新用户"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("无效的请求数据")
            return jsonify({
                'status': 'error',
                'message': '无效的请求数据'
            }), 400
            
        logger.info(f"接收到创建用户请求: {data}")
        
        # 检查必要字段
        required_fields = ['username', 'email', 'password', 'role']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            logger.warning(f"缺少必要字段: {missing_fields}")
            return jsonify({
                'status': 'error',
                'message': f'缺少必要字段: {", ".join(missing_fields)}'
            }), 400
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=data['username']).first():
            logger.warning(f"用户名已存在: {data['username']}")
            return jsonify({
                'status': 'error',
                'message': '用户名已存在'
            }), 400
            
        if User.query.filter_by(email=data['email']).first():
            logger.warning(f"邮箱已存在: {data['email']}")
            return jsonify({
                'status': 'error',
                'message': '邮箱已存在'
            }), 400
        
        # 验证字段长度
        if len(data['username']) > 80:
            return jsonify({
                'status': 'error',
                'message': '用户名长度不能超过80个字符'
            }), 400
            
        if len(data['email']) > 120:
            return jsonify({
                'status': 'error',
                'message': '邮箱长度不能超过120个字符'
            }), 400
            
        if len(data['role']) > 20:
            return jsonify({
                'status': 'error',
                'message': '角色长度不能超过20个字符'
            }), 400
        
        try:
            # 创建新用户
            password_hash = generate_password_hash(data['password'])
            
            # 检查密码哈希长度
            if len(password_hash) > 256:
                logger.warning(f"生成的密码哈希太长: {len(password_hash)} 字符")
                return jsonify({
                    'status': 'error',
                    'message': '密码哈希长度超出限制，请使用更短的密码'
                }), 400
                
            new_user = User(
                username=data['username'],
                email=data['email'],
                password_hash=password_hash,
                role=data['role'],
                is_active=data.get('is_active', True),
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            logger.info(f"成功创建用户: {new_user.username}")
            return jsonify({
                'status': 'success',
                'message': '用户创建成功',
                'data': new_user.to_dict()
            }), 201
            
        except pymysql.err.DataError as db_error:
            db.session.rollback()
            logger.error(f"数据库数据错误: {str(db_error)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'数据库数据错误: {str(db_error)}'
            }), 400
        except ValueError as val_error:
            db.session.rollback()
            logger.error(f"数据验证错误: {str(val_error)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': str(val_error)
            }), 400
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"数据库操作失败: {str(db_error)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'数据库操作失败: {str(db_error)}'
            }), 500
            
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'创建用户请求处理失败: {str(e)}'
        }), 500

@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(user_id):
    """更新用户信息"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404
            
        # 不允许修改admin用户
        if user.username == 'admin':
            return jsonify({
                'status': 'error',
                'message': '不能修改管理员用户'
            }), 403
        
        data = request.get_json()
        logger.info(f"接收到更新用户请求: user_id={user_id}, data={data}")
        
        # 更新用户信息
        if 'username' in data and data['username'] != user.username:
            if len(data['username']) > 80:
                return jsonify({
                    'status': 'error',
                    'message': '用户名长度不能超过80个字符'
                }), 400
                
            if User.query.filter_by(username=data['username']).first():
                return jsonify({
                    'status': 'error',
                    'message': '用户名已存在'
                }), 400
            user.username = data['username']
            
        if 'email' in data and data['email'] != user.email:
            if len(data['email']) > 120:
                return jsonify({
                    'status': 'error',
                    'message': '邮箱长度不能超过120个字符'
                }), 400
                
            if User.query.filter_by(email=data['email']).first():
                return jsonify({
                    'status': 'error',
                    'message': '邮箱已存在'
                }), 400
            user.email = data['email']
            
        if 'password' in data:
            password_hash = generate_password_hash(data['password'])
            # 检查密码哈希长度
            if len(password_hash) > 256:
                return jsonify({
                    'status': 'error',
                    'message': '密码哈希长度超出限制，请使用更短的密码'
                }), 400
            user.password_hash = password_hash
            
        if 'role' in data:
            if len(data['role']) > 20:
                return jsonify({
                    'status': 'error',
                    'message': '角色长度不能超过20个字符'
                }), 400
            user.role = data['role']
            
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        try:
            db.session.commit()
            logger.info(f"成功更新用户: {user.username}")
            
            return jsonify({
                'status': 'success',
                'message': '用户更新成功',
                'data': user.to_dict()
            }), 200
        except pymysql.err.DataError as db_error:
            db.session.rollback()
            logger.error(f"数据库数据错误: {str(db_error)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'数据库数据错误: {str(db_error)}'
            }), 400
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"数据库操作失败: {str(db_error)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'数据库操作失败: {str(db_error)}'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新用户失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(user_id):
    """删除用户"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404
            
        # 不允许删除admin用户和当前用户
        if user.username == 'admin':
            return jsonify({
                'status': 'error',
                'message': '不能删除管理员用户'
            }), 403
            
        current_user = request.user
        if user.id == current_user.id:
            return jsonify({
                'status': 'error',
                'message': '不能删除当前登录用户'
            }), 403
        
        try:
            db.session.delete(user)
            db.session.commit()
            logger.info(f"成功删除用户: {user.username}")
            
            return jsonify({
                'status': 'success',
                'message': '用户删除成功'
            }), 200
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"数据库操作失败: {str(db_error)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'数据库操作失败: {str(db_error)}'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除用户失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 