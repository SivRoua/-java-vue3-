from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from config.database import Base
import logging

logger = logging.getLogger(__name__)

class User(Base):
    """用户模型"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, comment='用户ID')
    username = Column(String(80), unique=True, nullable=False, comment='用户名')
    password_hash = Column(String(256), nullable=False, comment='密码哈希')
    email = Column(String(120), unique=True, nullable=False, comment='邮箱')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    role = Column(String(20), default='user', comment='用户角色')

    def __init__(self, username, password_hash, email, role='user', is_active=True, created_at=None):
        if username and len(username) > 80:
            raise ValueError("用户名长度不能超过80个字符")
        if email and len(email) > 120:
            raise ValueError("邮箱长度不能超过120个字符")
        if role and len(role) > 20:
            raise ValueError("角色长度不能超过20个字符")
        if password_hash and len(password_hash) > 256:
            raise ValueError("密码哈希长度不能超过256个字符")
            
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.role = role
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        """转换为字典"""
        try:
            return {
                'id': self.id,
                'username': self.username,
                'email': self.email,
                'is_active': self.is_active if self.is_active is not None else True,
                'role': self.role if self.role is not None else 'user',
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
        except Exception as e:
            logger.error(f"转换用户数据为字典时出错: {str(e)}")
            # 返回最小化的用户数据
            return {
                'id': self.id if hasattr(self, 'id') else None,
                'username': self.username if hasattr(self, 'username') else 'unknown',
                'email': self.email if hasattr(self, 'email') else None,
                'is_active': True,
                'role': 'user',
                'created_at': None
            }