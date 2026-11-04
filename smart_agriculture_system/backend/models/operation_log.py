from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = MetaData()

class OperationLog(Base):
    __tablename__ = 'operation_logs'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    operation_type = Column(String(50), nullable=False)
    device_type = Column(String(50))
    operation_time = Column(DateTime, default=datetime.utcnow)
    operation_result = Column(Boolean)
    description = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'operation_type': self.operation_type,
            'device_type': self.device_type,
            'operation_time': self.operation_time.isoformat() if self.operation_time else None,
            'operation_result': self.operation_result,
            'description': self.description
        }