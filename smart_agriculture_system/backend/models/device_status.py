from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = MetaData()

class DeviceStatus(Base):
    __tablename__ = 'device_status'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    device_type = Column(String(50), nullable=False)
    status = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = Column(String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_type': self.device_type,
            'status': bool(self.status),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'description': self.description
        }