from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models.sensor_data import SensorData
from models.threshold_settings import ThresholdSetting
from models.operation_log import OperationLog
from config.database import Config
import logging
import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class MonitorService:
    """监控服务，用于检查传感器数据并根据阈值触发警报"""
    
    def __init__(self, auto_control_service=None):
        """初始化监控服务"""
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.Session = sessionmaker(bind=self.engine)
        self.auto_control_service = auto_control_service
    
    def check_thresholds(self):
        """检查最新传感器数据是否触发了任何阈值警报"""
        session = self.Session()
        try:
            # 获取最新的传感器数据
            latest_data = session.query(SensorData).order_by(
                desc(SensorData.timestamp)
            ).first()
            
            if not latest_data:
                logger.warning("没有可用的传感器数据，无法进行阈值检查")
                return False
            
            # 获取所有启用的阈值设置
            enabled_thresholds = session.query(ThresholdSetting).filter(
                ThresholdSetting.enabled == True
            ).all()
            
            if not enabled_thresholds:
                logger.info("没有启用的阈值设置")
                return False
            
            alerts_triggered = False
            
            # 检查每个阈值设置
            for threshold in enabled_thresholds:
                triggered = self.check_single_threshold(threshold, latest_data, session)
                if triggered:
                    alerts_triggered = True
            
            return alerts_triggered
            
        except Exception as e:
            logger.error(f"检查阈值失败: {str(e)}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def check_single_threshold(self, threshold, sensor_data, session):
        """检查单个阈值设置是否被触发"""
        try:
            # 获取对应的传感器数据
            value = None
            threshold_type = threshold.type
            
            if threshold_type == 'temperature':
                value = sensor_data.air_temperature
            elif threshold_type == 'humidity':
                value = sensor_data.air_humidity
            elif threshold_type == 'soil_moisture':
                value = sensor_data.soil_moisture
            elif threshold_type == 'soil_temperature':
                value = sensor_data.soil_temperature
            elif threshold_type == 'light_intensity':
                value = sensor_data.light_intensity
            elif threshold_type == 'co2_level' or threshold_type == 'co2_concentration':
                value = sensor_data.co2_concentration
            
            if value is None:
                logger.warning(f"未找到类型为 {threshold_type} 的传感器数据")
                return False
            
            # 检查是否触发警报
            triggered = False
            if threshold.operator == '>':
                triggered = value > threshold.threshold
            elif threshold.operator == '<':
                triggered = value < threshold.threshold
            
            if triggered:
                # 记录警报
                self.log_alert(threshold, value, session)
                
                # 如果配置了自动控制服务，执行自动控制
                if self.auto_control_service:
                    actions = self.auto_control_service.process_threshold_alert(threshold, value)
                    if actions:
                        logger.info(f"自动控制已执行: {len(actions)} 个设备操作")
                        
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查单个阈值失败: {str(e)}")
            return False
    
    def log_alert(self, threshold, current_value, session):
        """记录警报到操作日志表"""
        try:
            # 获取警报信息
            if threshold.operator == '>':
                condition = "高于"
            elif threshold.operator == '<':
                condition = "低于"
            else:
                condition = threshold.operator
            
            # 获取阈值类型的中文名称
            type_names = {
                'temperature': '温度',
                'humidity': '湿度',
                'soil_moisture': '土壤湿度',
                'soil_temperature': '土壤温度',
                'light_intensity': '光照强度',
                'co2_level': 'CO2浓度',
                'co2_concentration': 'CO2浓度'
            }
            
            type_name = type_names.get(threshold.type, threshold.type)
            
            # 创建操作日志记录
            alert_log = OperationLog(
                user_id=threshold.user_id,
                operation_type=f"{threshold.name}警报",
                device_type=threshold.type,
                operation_time=datetime.datetime.utcnow(),
                operation_result=False,  # 警报为未处理状态
                description=f"{type_name}{condition}{threshold.threshold}，当前值为{current_value}"
            )
            
            session.add(alert_log)
            session.commit()
            
            logger.info(f"记录警报: {threshold.name}, 当前值: {current_value}")
            return True
            
        except Exception as e:
            logger.error(f"记录警报失败: {str(e)}")
            session.rollback()
            return False 