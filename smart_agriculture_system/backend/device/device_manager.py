import logging
import time
from typing import Dict, Any, Optional
from .wsn_client import WSNClient
from config.hardware_config import DEVICE_CONFIG, HARDWARE_CONFIG, RELAY_CONFIG

logger = logging.getLogger(__name__)

class DeviceManager:
    def __init__(self):
        self.wsn_client = WSNClient(
            HARDWARE_CONFIG['controller']['ip'],
            HARDWARE_CONFIG['controller']['port']
        )
        # 初始化设备状态字典，包含更多信息
        self.device_status = {}
        for device_type, config in DEVICE_CONFIG.items():
            self.device_status[device_type] = {
                'status': 0,  # 0=关闭, 1=开启
                'name': config.get('name', device_type),
                'description': config.get('description', ''),
                'type': device_type
            }
        self.last_sensor_data = {}
        self.last_data_time = 0
        self.data_freshness_threshold = 110  # 数据新鲜度阈值（秒），略小于获取间隔
        # 自动控制管理器将在应用初始化时创建
        
    def connect(self) -> bool:
        """连接到硬件控制器"""
        try:
            result = self.wsn_client.connect()
            if result:
                logger.info("成功连接到硬件控制器")
                # 连接成功后获取所有设备的当前状态
                self._update_all_device_status()
                # 初始化继电器状态缓存
                self._init_relay_status_cache()
            else:
                logger.warning("无法连接到硬件控制器，将在后续操作时重试")
            return result
        except Exception as e:
            logger.error(f"连接设备失败: {str(e)}")
            return False
            
    def disconnect(self) -> None:
        """断开硬件控制器连接"""
        try:
            self.wsn_client.disconnect()
            logger.info("已断开硬件控制器连接")
        except Exception as e:
            logger.error(f"断开设备连接失败: {str(e)}")
            
    def control_device(self, device_type: str, action: str) -> bool:
        """
        控制设备操作
        
        Args:
            device_type: 设备类型
            action: 操作类型 ('open' or 'close')
            
        Returns:
            bool: 操作是否成功
        """
        if device_type not in DEVICE_CONFIG:
            logger.error(f"未知设备类型: {device_type}")
            return False
            
        # 如果未连接，尝试连接
        if not self.wsn_client.connected:
            logger.info("控制设备前重新连接硬件控制器")
            if not self.connect():
                logger.error("无法连接到硬件控制器，无法控制设备")
                return False
            
        try:
            # 标准化操作名称
            action = action.lower()
            if action not in ['open', 'close']:
                logger.error(f"无效的操作类型: {action}，应为 'open' 或 'close'")
                return False
            
            # 获取设备配置信息
            device_config = DEVICE_CONFIG[device_type]
            device_name = device_config.get('name', device_type)
                
            # 首先更新本地设备状态，确保UI立即响应
            status_value = 1 if action == 'open' else 0
            self.device_status[device_type] = {
                'type': device_type,
                'status': status_value,
                'name': device_name,
                'description': device_config.get('description', '')
            }
            
            # 简化日志
            logger.info(f"控制设备: {device_name} ({action})")
            
            # 发送控制命令
            result = self.wsn_client.send_command(device_type, action)
            
            if not result:
                logger.warning(f"设备 {device_name} 控制命令可能未成功执行，但已更新本地状态")
            
            # 无论命令是否成功，都已经更新了设备状态
            return True
                
        except Exception as e:
            logger.error(f"控制设备 {device_type} 失败: {str(e)}")
            return False
            
    def get_device_status(self, device_type: Optional[str] = None) -> Dict[str, Any]:
        """获取设备状态"""
        if device_type:
            return self.device_status.get(device_type, None)
        return self.device_status
        
    def _update_all_device_status(self) -> None:
        """更新所有设备的状态"""
        try:
            logger.info("正在更新所有设备状态")
            
            # 设备状态更新计数
            updated_count = 0
            default_count = 0
            
            # 遍历所有设备，确保每个设备都有状态记录
            for device_type, config in DEVICE_CONFIG.items():
                # 如果设备状态不存在，创建默认状态（关闭）
                if device_type not in self.device_status:
                    self.device_status[device_type] = {
                        'status': 0,  # 默认关闭
                        'name': config.get('name', device_type),
                        'description': config.get('description', ''),
                        'type': device_type
                    }
                    default_count += 1
                else:
                    # 尝试从硬件查询设备状态
                    try:
                        if self.wsn_client.connected:
                            status = self.wsn_client.query_device_status(device_type)
                            if status is not None:
                                # 更新设备状态
                                self.device_status[device_type]['status'] = status
                                updated_count += 1
                            # 不再为每个设备单独记录日志
                        # 不再为每个设备单独记录日志
                    except Exception as e:
                        logger.warning(f"查询设备 {device_type} 状态失败: {str(e)}")
            
            # 使用汇总信息代替多个日志
            logger.info(f"设备状态更新完成: {updated_count}个设备已更新状态, {default_count}个设备使用默认状态")
            
            # 尝试发送一个ping命令，确认连接状态
            if self.wsn_client.ping():
                logger.info("与硬件控制器的连接正常")
            else:
                logger.warning("与硬件控制器的连接可能不稳定")
            
        except Exception as e:
            logger.error(f"更新所有设备状态失败: {str(e)}")
            # 出错时不要清空设备状态，保持现有状态
        
    def get_sensor_data(self) -> Dict[str, float]:
        """获取传感器数据"""
        current_time = time.time()
        
        # 判断缓存的数据是否足够新鲜
        if self.last_sensor_data and current_time - self.last_data_time < self.data_freshness_threshold:
            logger.debug("使用缓存的传感器数据")
            return self.last_sensor_data
            
        # 如果未连接，尝试连接
        if not self.wsn_client.connected:
            logger.info("获取传感器数据前重新连接硬件控制器")
            if not self.connect():
                logger.error("无法连接到硬件控制器，返回空数据")
                return self._get_default_sensor_data()
        
        try:
            logger.info("正在从硬件控制器获取传感器数据")
            data = self.wsn_client.get_sensor_data()
            
            # 检查数据完整性
            if not data:
                logger.warning("获取到的传感器数据为空，返回默认值")
                return self._get_default_sensor_data()
                
            # 验证和处理数据
            result = self._process_sensor_data(data)
            
            # 更新缓存
            self.last_sensor_data = result
            self.last_data_time = current_time
            
            return result
        except Exception as e:
            logger.error(f"获取传感器数据失败: {str(e)}")
            return self._get_default_sensor_data()
            
    def _process_sensor_data(self, data: Dict[str, Any]) -> Dict[str, float]:
        """处理传感器数据，确保所有字段存在并为正确类型"""
        result = {}
        
        # 定义传感器字段和默认值
        expected_fields = {
            'air_temperature': 0.0, 
            'air_humidity': 0.0, 
            'soil_temperature': 0.0, 
            'soil_moisture': 0.0,
            'light_intensity': 0.0, 
            'co2_concentration': 0.0
        }
        
        for field, default in expected_fields.items():
            # 获取数据，如果不存在或类型错误则使用默认值
            try:
                value = data.get(field, default)
                if value is None or not isinstance(value, (int, float)):
                    logger.warning(f"传感器数据 {field} 类型错误或为None，使用默认值")
                    value = default
                result[field] = float(value)  # 确保所有值为float类型
            except Exception as e:
                logger.error(f"处理传感器数据字段 {field} 时出错: {str(e)}")
                result[field] = default
                
        return result
        
    def _get_default_sensor_data(self) -> Dict[str, float]:
        """返回默认的传感器数据（全为0）"""
        return {
            'air_temperature': 0.0,
            'air_humidity': 0.0,
            'soil_temperature': 0.0,
            'soil_moisture': 0.0,
            'light_intensity': 0.0,
            'co2_concentration': 0.0
        }
        
    def _init_relay_status_cache(self) -> None:
        """初始化继电器状态缓存，基于当前设备状态"""
        try:
            logger.info("初始化继电器状态缓存")
            
            # 按继电器地址分组设备
            relay_devices = {}
            for device_type, config in DEVICE_CONFIG.items():
                relay_id = config.get('relay_address')
                if relay_id not in relay_devices:
                    relay_devices[relay_id] = []
                relay_devices[relay_id].append((device_type, config.get('relay_port')))
            
            # 为每个继电器初始化状态
            for relay_id, devices in relay_devices.items():
                relay_status = [0, 0, 0, 0]  # 默认所有通道关闭
                
                # 根据设备状态设置继电器通道状态
                for device_type, port in devices:
                    if device_type in self.device_status:
                        # 端口号从1开始，数组索引从0开始，需要调整
                        if isinstance(port, str) and port.startswith('0x'):
                            port_index = int(port, 16) - 1
                        else:
                            port_index = int(port) - 1
                            
                        if 0 <= port_index < 4:
                            # 设置通道状态
                            relay_status[port_index] = self.device_status[device_type]['status']
                
                # 更新继电器状态缓存
                self.wsn_client.relay_status_cache[relay_id] = relay_status
                
            # 只输出一条汇总日志
            logger.info(f"初始化了 {len(relay_devices)} 个继电器的状态缓存")
                
        except Exception as e:
            logger.error(f"初始化继电器状态缓存失败: {str(e)}")
            
    def get_connection_status(self) -> Dict[str, Any]:
        """获取设备连接状态"""
        if not self.wsn_client:
            return {
                'connected': False,
                'status': 'disconnected',
                'message': '控制器未初始化',
                'last_connection': None,
                'last_communication': None,
                'connected_devices': 0,
                'total_devices': len(DEVICE_CONFIG)
            }
            
        # 尝试通过ping测试连接
        ping_result = self.wsn_client.ping() if self.wsn_client.connected else False
        
        if ping_result:
            # 成功ping通，连接正常
            # 统计在线设备数量（暂时返回所有设备作为假设）
            connected_devices = len(DEVICE_CONFIG) if ping_result else 0
            
            return {
                'connected': True,
                'status': 'connected',
                'message': '已连接',
                'last_connection': self.wsn_client.last_connection_time,
                'last_communication': self.wsn_client.last_communication_time,
                'connected_devices': connected_devices,
                'total_devices': len(DEVICE_CONFIG)
            }
        else:
            # 尝试重新连接
            if not self.wsn_client.connected:
                logger.info("检测到设备未连接，尝试重新连接")
                connect_result = self.connect()
                
                if connect_result:
                    # 重新连接成功
                    return {
                        'connected': True,
                        'status': 'connected',
                        'message': '已连接',
                        'last_connection': self.wsn_client.last_connection_time,
                        'last_communication': self.wsn_client.last_communication_time,
                        'connected_devices': len(DEVICE_CONFIG),
                        'total_devices': len(DEVICE_CONFIG)
                    }
            
            # 仍然失败
            return {
                'connected': False,
                'status': 'disconnected',
                'message': '未连接',
                'last_connection': self.wsn_client.last_connection_time,
                'last_communication': self.wsn_client.last_communication_time,
                'connected_devices': 0,
                'total_devices': len(DEVICE_CONFIG)
            }