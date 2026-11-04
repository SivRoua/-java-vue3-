from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import logging

logger = logging.getLogger(__name__)

# 初始化 SQLAlchemy
db = SQLAlchemy()

# 初始化 JWT
jwt = JWTManager()

def init_extensions(app):
    """初始化所有扩展"""
    try:
        # 初始化 SQLAlchemy
        db.init_app(app)
        logger.info("SQLAlchemy 初始化成功")
        
        # 初始化 JWT
        jwt.init_app(app)
        logger.info("JWT 初始化成功")
    except Exception as e:
        logger.error(f"初始化扩展失败: {str(e)}")
        raise 