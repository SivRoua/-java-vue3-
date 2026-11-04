import logging
from typing import Dict, Any, List, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.database import Config
from models.threshold_settings import ThresholdSetting
from models.operation_log import OperationLog
from device.device_manager import DeviceManager
import datetime

logger = logging.getLogger(__name__)

class AutoControlService:
    """自动控制服务，根据警报自动控制设备"""
    
    def __init__(self, device_manager: DeviceManager):
        """初始化自动控制服务"""
        self.device_manager = device_manager
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.Session = sessionmaker(bind=self.engine)
        
        # 定义控制规则：{监测类型: [(条件运算符, 阈值, 设备类型, 操作)]}
        self.control_rules = {
            'temperature': [
                ('>', 50, 'external_fan', 'open'),   # 温度高于50度，开启外部风扇
                ('>', 50, 'internal_fan', 'open'),   # 温度高于50度，开启内部风扇
                ('>', 50, 'external_shade', 'open'), # 温度高于50度，开启外遮阳
                ('>', 50, 'internal_shade', 'open'), # 温度高于50度，开启内遮阳
                ('>', 50, 'skylight', 'open'),       # 温度高于50度，开启天窗
                ('<', 10, 'external_fan', 'close'),  # 温度低于10度，关闭外部风扇
                ('<', 10, 'internal_fan', 'close'),  # 温度低于10度，关闭内部风扇
                ('<', 10, 'external_shade', 'close'),# 温度低于10度，关闭外遮阳
                ('<', 10, 'internal_shade', 'close') # 温度低于10度，关闭内遮阳
            ],
            'humidity': [
                ('>', 80, 'water_curtain', 'close'), # 湿度高于80%，关闭水帘
                ('>', 80, 'spray', 'close'),         # 湿度高于80%，关闭喷灌
                ('<', 30, 'water_curtain', 'open'),  # 湿度低于30%，开启水帘
                ('<', 30, 'spray', 'open')           # 湿度低于30%，开启喷灌
            ],
            'soil_moisture': [
                ('<', 20, 'spray', 'open'),          # 土壤湿度低于20%，开启喷灌
                ('>', 80, 'spray', 'close')          # 土壤湿度高于80%，关闭喷灌
            ],
            'light_intensity': [
                ('<', 1000, 'light', 'open'),        # 光照强度低于1000，开启灯光
                ('>', 8000, 'external_shade', 'open'),# 光照强度高于8000，开启外遮阳
                ('>', 8000, 'internal_shade', 'open') # 光照强度高于8000，开启内遮阳
            ],
            'co2_concentration': [
                ('>', 3000, 'skylight', 'open'),     # CO2浓度高于3000ppm，开启天窗
                ('>', 3000, 'external_fan', 'open'),  # CO2浓度高于3000ppm，开启外部风扇
                ('>', 3000, 'internal_fan', 'open')   # CO2浓度高于3000ppm，开启内部风扇
            ]
        }
        
    def handle_alert(self, alert_type: str, current_value: float, threshold_value: float, operator: str) -> List[Dict[str, Any]]:
        """
        处理警报并自动控制相关设备
        
        Args:
            alert_type: 警报类型 (temperature, humidity, soil_moisture等)
            current_value: 当前传感器值
            threshold_value: 阈值
            operator: 操作符 ('>', '<', '>=', '<=', '==')
            
        Returns:
            List[Dict[str, Any]]: 已执行的设备控制操作列表
        """
        if alert_type not in self.control_rules:
            logger.warning(f"未找到类型 {alert_type} 的自动控制规则")
            return []
            
        # 获取此类型的所有控制规则
        rules = self.control_rules[alert_type]
        executed_actions = []
        
        # 检查每个规则是否适用
        for rule_operator, rule_threshold, device_type, action in rules:
            # 检查规则条件是否匹配当前警报
            if rule_operator == operator and abs(rule_threshold - threshold_value) < 0.1:
                # 执行设备控制
                logger.info(f"自动控制：由于{alert_type}{operator}{threshold_value}，{action} {device_type}")
                result = self.device_manager.control_device(device_type, action)
                
                if result:
                    executed_actions.append({
                        'device_type': device_type,
                        'action': action,
                        'result': True
                    })
                    # 记录自动控制操作
                    self._log_auto_control(alert_type, current_value, threshold_value, device_type, action)
                else:
                    logger.error(f"自动控制设备 {device_type} 失败")
                    executed_actions.append({
                        'device_type': device_type,
                        'action': action,
                        'result': False
                    })
                    
        return executed_actions
    
    def process_threshold_alert(self, threshold: ThresholdSetting, current_value: float) -> List[Dict[str, Any]]:
        """
        处理特定阈值警报，执行相应的自动控制
        
        Args:
            threshold: 阈值设置对象
            current_value: 当前传感器值
            
        Returns:
            List[Dict[str, Any]]: 已执行的设备控制操作列表
        """
        return self.handle_alert(
            threshold.type,
            current_value,
            threshold.threshold,
            threshold.operator
        )
    
    def _log_auto_control(self, alert_type: str, current_value: float, 
                         threshold_value: float, device_type: str, action: str) -> None:
        """记录自动控制操作到数据库"""
        session = self.Session()
        try:
            # 获取警报信息
            if action == 'open':
                action_desc = "开启"
            else:
                action_desc = "关闭"
                
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
            
            device_names = {
                'external_fan': '外通风',
                'internal_fan': '内通风',
                'external_shade': '外遮阳',
                'internal_shade': '内遮阳',
                'skylight': '天窗',
                'spray': '喷灌',
                'water_curtain': '水帘',
                'light': '灯光'
            }
            
            type_name = type_names.get(alert_type, alert_type)
            device_name = device_names.get(device_type, device_type)
            
            # 创建操作日志记录
            log = OperationLog(
                user_id=None,  # 自动控制，无用户ID
                operation_type="自动控制",
                device_type=device_type,
                operation_time=datetime.datetime.utcnow(),
                operation_result=True,
                description=f"由于{type_name}值为{current_value}，自动{action_desc}{device_name}"
            )
            
            session.add(log)
            session.commit()
            
            logger.info(f"记录自动控制: {device_type} {action}")
            
        except Exception as e:
            logger.error(f"记录自动控制操作失败: {str(e)}")
            session.rollback()
        finally:
            session.close()