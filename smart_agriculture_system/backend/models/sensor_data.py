from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = MetaData()

class SensorData(Base):
    __tablename__ = 'sensor_data'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    air_temperature = Column(Float)
    air_humidity = Column(Float)
    soil_temperature = Column(Float)
    soil_moisture = Column(Float)
    light_intensity = Column(Float)
    co2_concentration = Column(Float)
    
    def to_dict(self):
        """将对象转换为字典，添加兼容字段"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'air_temperature': self.air_temperature,
            'air_humidity': self.air_humidity,
            'soil_temperature': self.soil_temperature,
            'soil_moisture': self.soil_moisture,
            'light_intensity': self.light_intensity,
            'co2_concentration': self.co2_concentration,
            
            # 添加兼容字段，与前端对应
            'temperature': self.air_temperature,
            'humidity': self.air_humidity,
            'co2_level': self.co2_concentration
        }