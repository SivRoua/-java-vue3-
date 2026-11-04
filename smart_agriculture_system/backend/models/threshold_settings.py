from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from config.database import Base
import datetime

class ThresholdSetting(Base):
    """阈值设置（警报规则）模型"""
    __tablename__ = 'threshold_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment='规则名称')
    type = Column(String(20), nullable=False, comment='监测类型')
    operator = Column(String(5), nullable=False, comment='触发条件操作符')
    threshold = Column(Float, nullable=False, comment='阈值')
    enabled = Column(Boolean, default=True, comment='是否启用')
    create_time = Column(DateTime, default=datetime.datetime.utcnow, comment='创建时间')
    update_time = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, comment='更新时间')
    user_id = Column(Integer, nullable=True, comment='创建者ID')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'operator': self.operator,
            'threshold': self.threshold,
            'enabled': self.enabled,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'user_id': self.user_id
        } 