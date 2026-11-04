import logging
import time
import threading
from typing import Dict, Any, List, Tuple
from .device_manager import DeviceManager
from config.hardware_config import DEVICE_CONFIG

logger = logging.getLogger(__name__)

class AutoControlManager:
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.is_auto_control_enabled = False
        self.control_thread = None
        self.should_stop = threading.Event()
        
        # 设置默认阈值
        self.thresholds = {
            'air_temperature': (20, 40),  # (最小值, 最大值)
            'air_humidity': (40, 60),
            'soil_temperature': (20, 40),
            'soil_moisture': (40, 60),
            'light_intensity': (4000, 6000),
            'co2_concentration': (400, 600)
        }
        
        # 设备控制映射
        self.device_mapping = {
            'air_temperature': ('external_fan', 1),  # (设备类型, 关联的继电器通道)
            'air_humidity': ('internal_fan', 2),
            'soil_temperature': ('skylight', 3),
            'soil_moisture': ('spray', 4),
            'light_intensity': ('light', 1),
            'co2_concentration': ('water_curtain', 2)
        }
    
    def start_auto_control(self) -> bool:
        """
        启动自动控制线程
        
        Returns:
            bool: 启动是否成功
        """
        if self.is_auto_control_enabled:
            logger.warning("自动控制已经在运行中")
            return True
        
        try:
            logger.info("启动自动控制")
            self.is_auto_control_enabled = True
            self.should_stop.clear()
            
            # 创建并启动控制线程
            self.control_thread = threading.Thread(
                target=self._auto_control_loop,
                daemon=True  # 设置为守护线程，主线程结束时自动结束
            )
            self.control_thread.start()
            logger.info("自动控制线程已启动")
            return True
        except Exception as e:
            logger.error(f"启动自动控制失败: {str(e)}")
            self.is_auto_control_enabled = False
            return False
    
    def stop_auto_control(self) -> bool:
        """
        停止自动控制线程
        
        Returns:
            bool: 停止是否成功
        """
        if not self.is_auto_control_enabled:
            logger.warning("自动控制未启动")
            return True
        
        try:
            logger.info("停止自动控制")
            self.is_auto_control_enabled = False
            self.should_stop.set()
            
            # 等待线程结束
            if self.control_thread and self.control_thread.is_alive():
                self.control_thread.join(timeout=5)
                if self.control_thread.is_alive():
                    logger.warning("自动控制线程未能在5秒内停止")
                else:
                    logger.info("自动控制线程已停止")
            
            self.control_thread = None
            return True
        except Exception as e:
            logger.error(f"停止自动控制失败: {str(e)}")
            return False
    
    def update_thresholds(self, new_thresholds: Dict[str, Tuple[int, int]]) -> bool:
        """
        更新控制阈值
        
        Args:
            new_thresholds: 新的阈值设置，格式为 {传感器类型: (最小值, 最大值)}
            
        Returns:
            bool: 更新是否成功
        """
        try:
            for sensor_type, threshold in new_thresholds.items():
                if sensor_type in self.thresholds:
                    min_val, max_val = threshold
                    # 验证阈值的有效性
                    if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
                        logger.error(f"无效的阈值类型: {sensor_type} {threshold}")
                        continue
                    if min_val >= max_val:
                        logger.error(f"无效的阈值范围: {sensor_type} {threshold}")
                        continue
                    
                    self.thresholds[sensor_type] = (min_val, max_val)
                    logger.info(f"已更新 {sensor_type} 阈值为 {threshold}")
                else:
                    logger.warning(f"未知的传感器类型: {sensor_type}")
            
            logger.info(f"阈值更新完成: {self.thresholds}")
            return True
        except Exception as e:
            logger.error(f"更新阈值失败: {str(e)}")
            return False
    
    def get_thresholds(self) -> Dict[str, Tuple[int, int]]:
        """
        获取当前阈值设置
        
        Returns:
            Dict: 当前阈值设置
        """
        return self.thresholds
    
    def is_enabled(self) -> bool:
        """
        获取自动控制是否启用
        
        Returns:
            bool: 自动控制是否启用
        """
        return self.is_auto_control_enabled
    
    def _auto_control_loop(self) -> None:
        """
        自动控制循环
        """
        logger.info("自动控制循环开始运行")
        
        while not self.should_stop.is_set():
            try:
                # 检查连接状态
                if not self.device_manager.wsn_client.connected:
                    logger.warning("设备未连接，尝试重新连接...")
                    self.device_manager.connect()
                    if not self.device_manager.wsn_client.connected:
                        logger.error("无法连接到设备，自动控制暂停")
                        time.sleep(10)  # 等待10秒后重试
                        continue
                
                # 获取传感器数据
                sensor_data = self.device_manager.get_sensor_data()
                if not sensor_data:
                    logger.warning("无法获取传感器数据，跳过当前控制周期")
                    time.sleep(5)  # 等待5秒后重试
                    continue
                
                logger.info(f"获取到传感器数据: {sensor_data}")
                
                # 根据阈值控制设备
                self._control_devices_by_thresholds(sensor_data)
                
                # 等待一段时间后继续下一轮控制
                time.sleep(30)  # 控制频率：30秒一次
            except Exception as e:
                logger.error(f"自动控制循环出错: {str(e)}")
                time.sleep(10)  # 出错后等待10秒
        
        logger.info("自动控制循环已停止")
    
    def _control_devices_by_thresholds(self, sensor_data: Dict[str, float]) -> None:
        """
        根据阈值控制设备
        
        Args:
            sensor_data: 传感器数据
        """
        for sensor_type, (device_type, _) in self.device_mapping.items():
            if sensor_type not in sensor_data or sensor_type not in self.thresholds:
                continue
            
            current_value = sensor_data[sensor_type]
            min_threshold, max_threshold = self.thresholds[sensor_type]
            
            try:
                # 获取设备当前状态
                device_status = self.device_manager.get_device_status(device_type)
                current_status = device_status.get('status', 0) if device_status else 0
                
                # 根据阈值判断是否需要控制设备
                if current_value > max_threshold and current_status == 0:
                    # 当前值超过最大阈值且设备关闭时，打开设备
                    logger.info(f"{sensor_type} 值 {current_value} 超过最大阈值 {max_threshold}，开启 {device_type}")
                    self.device_manager.control_device(device_type, 'open')
                elif current_value < min_threshold and current_status == 1:
                    # 当前值低于最小阈值且设备打开时，关闭设备
                    logger.info(f"{sensor_type} 值 {current_value} 低于最小阈值 {min_threshold}，关闭 {device_type}")
                    self.device_manager.control_device(device_type, 'close')
            except Exception as e:
                logger.error(f"控制设备 {device_type} 失败: {str(e)}")