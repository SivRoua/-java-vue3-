import socket
import json
import logging
import time
import datetime
from typing import Dict, Any, Optional
from config.hardware_config import DEVICE_CONFIG

logger = logging.getLogger(__name__)

class WSNClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.connection_retries = 5  # 增加重试次数
        self.retry_delay = 3  # seconds，增加重试延迟
        self.socket_timeout = 10  # 增加套接字超时时间
        self.last_connection_time = None  # 上次成功连接时间
        self.last_communication_time = None  # 上次成功通信时间
        # 添加继电器状态缓存，用于跟踪每个继电器的当前状态
        self.relay_status_cache = {}
        
    def connect(self) -> bool:
        """连接到WSN网络"""
        for attempt in range(self.connection_retries):
            try:
                # 关闭之前的连接（如果有）
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                
                # 创建新的套接字
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.socket_timeout)  # 使用更长的超时时间
                logger.info(f"尝试连接到WSN网络: {self.host}:{self.port} (尝试 {attempt+1}/{self.connection_retries})")
                self.socket.connect((self.host, self.port))
                self.connected = True
                self.last_connection_time = datetime.datetime.now().isoformat()
                self.last_communication_time = self.last_connection_time
                logger.info(f"成功连接到WSN网络: {self.host}:{self.port}")
                
                # 连接成功后清空继电器状态缓存
                self.relay_status_cache = {}
                
                # 连接成功后，发送一个简单的Ping命令测试通信
                try:
                    # 使用kv_wsn库中的Ping格式：A5 00 00 FF FF FF FF FF 5A
                    ping_cmd = bytearray([0xA5, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x5A])
                    self.socket.send(ping_cmd)
                    logger.info("发送Ping命令测试通信")
                    
                    # 等待响应但不处理
                    self.socket.settimeout(2)
                    try:
                        response = self.socket.recv(1024)
                        if response:
                            logger.info(f"收到Ping响应: {' '.join([f'{b:02X}' for b in response])}")
                            self.last_communication_time = datetime.datetime.now().isoformat()
                    except socket.timeout:
                        logger.warning("Ping响应超时，但继续连接")
                except Exception as e:
                    logger.warning(f"Ping测试失败，但仍继续: {str(e)}")
                
                return True
            except socket.timeout:
                logger.error(f"连接WSN网络超时 (尝试 {attempt+1}/{self.connection_retries})")
            except ConnectionRefusedError:
                logger.error(f"连接被拒绝，确认设备是否开启并且IP和端口正确: {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"连接WSN网络失败: {str(e)}")
            
            if attempt < self.connection_retries - 1:
                logger.info(f"将在{self.retry_delay}秒后重试连接")
                time.sleep(self.retry_delay)
        
        self.connected = False
        logger.error(f"多次尝试后无法连接到WSN网络，请检查设备和网络设置")
        return False
            
    def disconnect(self) -> None:
        """断开WSN网络连接"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("已断开WSN网络连接")
            except Exception as e:
                logger.error(f"断开WSN网络连接失败: {str(e)}")
            finally:
                self.socket = None
                self.connected = False
                
    def get_current_relay_status(self, relay_id: int) -> list:
        """
        获取当前继电器的状态
        如果缓存中没有，则返回默认值 [0,0,0,0]
        
        Args:
            relay_id: 继电器ID
            
        Returns:
            list: 四个通道的状态列表 [ch1, ch2, ch3, ch4]
        """
        if relay_id in self.relay_status_cache:
            logger.info(f"使用缓存的继电器状态: {self.relay_status_cache[relay_id]}")
            return self.relay_status_cache[relay_id]
        
        # 默认所有通道关闭
        logger.info(f"继电器 {relay_id} 没有缓存状态，返回默认值 [0,0,0,0]")
        return [0, 0, 0, 0]
                
    def debug_print_response(self, response: bytes, operation: str = ""):
        """打印详细的响应信息，用于调试"""
        try:
            # 只在DEBUG级别打印完整的十六进制响应
            if logger.getEffectiveLevel() <= logging.DEBUG:
                hex_response = ' '.join([f'{b:02X}' for b in response])
                logger.debug(f"收到{operation}响应数据: {hex_response}")
            
            # 检查是否是继电器协议响应 (A5...5A)
            if len(response) >= 10 and response[0] == 0xA5 and response[9] == 0x5A:
                logger.debug(f"继电器地址: 0x{(response[2] << 8 | response[3]):04X}, 状态: {response[5:9]}")
            # 检查是否是传感器数据格式 (B5...5B)
            elif len(response) >= 9 and response[0] == 0xB5 and response[8] == 0x5B:
                sensor_type = response[1]
                sensor_addr = response[2]
                sensor_data = response[3:8]
                
                sensor_type_str = ""
                if sensor_type == 0x31:
                    sensor_type_str = "温度"
                elif sensor_type == 0x32:
                    sensor_type_str = "湿度"
                elif sensor_type == 0x33:
                    sensor_type_str = "二氧化碳"
                elif sensor_type == 0x34:
                    sensor_type_str = "光照度"
                else:
                    sensor_type_str = f"未知类型(0x{sensor_type:02X})"
                    
                # 降低日志级别为DEBUG
                logger.debug(f"传感器类型: {sensor_type_str} (0x{sensor_type:02X}), 地址: 0x{sensor_addr:02X}")
            else:
                logger.warning(f"未知的响应格式")
        except Exception as e:
            logger.error(f"解析响应数据失败: {str(e)}")
                
    def send_command(self, device_type: str, action: str) -> bool:
        """发送控制命令"""
        if not self.connected:
            logger.error("未连接到WSN网络，尝试重新连接...")
            if not self.connect():
                return False
            
        try:
            # 从配置中获取设备的继电器地址和端口
            device_config = DEVICE_CONFIG.get(device_type.lower())
            if not device_config:
                logger.error(f"未知的设备类型: {device_type}")
                return False
                
            device_id = device_config.get('relay_address')
            device_port = device_config.get('relay_port')
            
            if device_id is None or device_port is None:
                logger.error(f"设备 {device_type} 缺少继电器地址或端口配置")
                return False
                
            # 动作值: 开=1, 关=0
            action_value = 1 if action.lower() == 'open' else 0
            
            logger.info(f"设备 {device_type} 控制: 地址=0x{device_id:04X}, 端口={device_port}, 动作={'开启' if action_value else '关闭'}")
            
            # 端口号从1开始，数组索引从0开始，需要调整
            if isinstance(device_port, str) and device_port.startswith('0x'):
                port_index = int(device_port, 16) - 1
            else:
                port_index = int(device_port) - 1
                
            # 确保端口索引在有效范围内
            if not (0 <= port_index < 4):
                logger.error(f"无效的端口索引: {port_index}，有效范围为0-3")
                return False
                
            # 获取当前继电器的状态，保持其他通道的状态不变
            relay_status = self.get_current_relay_status(device_id)
            # 设置指定通道的状态
            relay_status[port_index] = action_value
            # 更新缓存
            self.relay_status_cache[device_id] = relay_status.copy()
            logger.info(f"更新继电器 {device_id} 状态缓存: {relay_status}")
            
            # 使用make_relay_command生成命令
            command = self.make_relay_command(device_id, relay_status)
            if not command:
                logger.error("生成继电器命令失败")
                return False
                
            logger.info(f"发送继电器控制命令: {' '.join([f'{b:02X}' for b in command])}")
            
            # 确保套接字连接有效
            if not self.socket:
                logger.error("套接字连接无效，尝试重新连接")
                if not self.connect():
                    return False
            
            # 发送命令前先清空接收缓冲区
            try:
                self.socket.settimeout(0.1)
                while True:
                    try:
                        data = self.socket.recv(1024)
                        if not data:
                            break
                    except (socket.timeout, BlockingIOError):
                        break
            except Exception as e:
                logger.warning(f"清空接收缓冲区时出错: {str(e)}")
            
            # 重置套接字超时并发送命令
            self.socket.settimeout(5)  # 增加超时时间
            
            # 发送命令
            self.socket.send(command)
            logger.info(f"已发送命令到设备 {device_type}")
            
            # 更新最后通信时间
            self.last_communication_time = datetime.datetime.now().isoformat()
            
            # 等待响应，但不阻塞太久
            try:
                response = self.socket.recv(1024)
                
                if response:
                    # 再次更新最后通信时间
                    self.last_communication_time = datetime.datetime.now().isoformat()
                
                    # 打印详细的响应信息
                    self.debug_print_response(response, f"{device_type}控制")
                    
                    # 检查是否是继电器协议响应 (A5...5A)
                    if len(response) >= 10 and response[0] == 0xA5 and response[9] == 0x5A:
                        # 验证地址匹配
                        resp_addr = (response[2] << 8) | response[3]
                        if resp_addr == device_id:
                            logger.info(f"命令执行成功: {device_type} {action}")
                            return True
                        else:
                            logger.warning(f"收到的响应地址(0x{resp_addr:04X})与请求地址(0x{device_id:04X})不匹配")
                            # 虽然地址不匹配，但我们假设命令已经执行
                            return True
                    else:
                        logger.warning(f"收到非标准响应，但仍视为成功: {' '.join([f'{b:02X}' for b in response])}")
                        return True
                else:
                    logger.warning("未收到设备控制响应，但命令可能已执行")
                    # 虽然没有收到响应，但我们假设命令已经发送成功
                    return True
            except socket.timeout:
                logger.warning(f"设备 {device_type} 控制命令响应超时，但命令可能已执行")
                # 超时不意味着命令没有执行，只是没有收到响应
                return True
                
        except Exception as e:
            logger.error(f"控制设备失败: {str(e)}")
            self.connected = False  # 标记为断开连接，下次操作时将尝试重连
            return False
            
    def query_device_status(self, device_type: str) -> Optional[int]:
        """查询设备状态"""
        if not self.connected:
            logger.error("未连接到WSN网络，尝试重新连接...")
            if not self.connect():
                return None
                
        try:
            # 从配置中获取设备的继电器地址和端口
            device_config = DEVICE_CONFIG.get(device_type.lower())
            if not device_config:
                logger.error(f"未知的设备类型: {device_type}")
                return None
                
            device_id = device_config.get('relay_address')
            device_port = device_config.get('relay_port')
            
            if device_id is None or device_port is None:
                logger.error(f"设备 {device_type} 缺少继电器地址或端口配置")
                return None
                
            # 端口号从1开始，数组索引从0开始，需要调整
            # 根据图片，端口值可能是十六进制值，需要转换
            if isinstance(device_port, str) and device_port.startswith('0x'):
                port_index = int(device_port, 16) - 1
            else:
                port_index = int(device_port) - 1
                
            # 确保端口索引在有效范围内
            if not (0 <= port_index < 4):
                logger.error(f"无效的端口索引: {port_index}，有效范围为0-3")
                return None
                
            logger.info(f"查询设备 {device_type} 状态: 地址=0x{device_id:04X}, 端口={device_port}, 端口索引={port_index}")
            
            # 构建查询命令：按照kv_wsn虚拟平台协议
            # 查询命令格式：A5 00 addr FF FF FF FF FF 5A
            command = bytearray([0xA5, 0x00, device_id & 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x5A])
            
            logger.debug(f"发送继电器状态查询命令: {' '.join([f'{b:02X}' for b in command])}")
            self.socket.send(command)
            
            # 更新最后通信时间
            self.last_communication_time = datetime.datetime.now().isoformat()
            
            # 设置接收超时，减少超时时间以提高响应速度
            self.socket.settimeout(3)
            
            try:
                response = self.socket.recv(1024)
                
                if response:
                    # 再次更新最后通信时间
                    self.last_communication_time = datetime.datetime.now().isoformat()
                
                    # 打印详细的响应信息
                    self.debug_print_response(response, f"{device_type}状态查询")
                    
                    # 解析继电器状态
                    relay_status = self.get_relay_status(response)
                    
                    # 检查是否获取到有效的继电器状态
                    if relay_status and 0 <= port_index < len(relay_status):
                        # 更新继电器状态缓存
                        self.relay_status_cache[device_id] = relay_status.copy()
                        logger.info(f"更新继电器 {device_id} 状态缓存: {relay_status}")
                        
                        # 返回对应端口的状态：1=开启，0=关闭
                        status = 1 if relay_status[port_index] else 0
                        logger.info(f"设备 {device_type} 状态: {status} ({'开启' if status == 1 else '关闭'})")
                        return status
                    else:
                        # 如果收到的是传感器数据而不是继电器状态
                        if len(response) >= 9 and response[0] == 0xB5 and response[8] == 0x5B:
                            logger.info(f"收到传感器数据而不是继电器状态，默认设备为关闭状态")
                            return 0
                        else:
                            logger.warning(f"无法获取设备 {device_type} 的状态，返回默认值0（关闭）")
                            return 0
            except socket.timeout:
                logger.error(f"查询设备 {device_type} 状态超时，返回默认状态0（关闭）")
                # 超时不一定意味着连接断开，只是当前命令没有响应
                # 不要将connected设为False，避免频繁重连
                return 0
                
        except Exception as e:
            logger.error(f"查询设备 {device_type} 状态失败: {str(e)}")
            self.connected = False  # 标记为断开连接，下次操作时将尝试重连
            return None
            
    def get_sensor_data(self) -> Dict[str, float]:
        """获取传感器数据"""
        if not self.connected:
            logger.error("未连接到WSN网络，尝试重新连接...")
            if not self.connect():
                return {}
            
        try:
            # 使用WSN协议格式发送Ping命令以获取传感器数据
            command = b'\xA5\x00\x00\xFF\xFF\xFF\xFF\xFF\x5A'
            logger.debug(f"发送WSN协议Ping命令获取传感器数据")
            self.socket.send(command)
            
            # 更新最后通信时间
            self.last_communication_time = datetime.datetime.now().isoformat()
            
            # 设置接收超时
            self.socket.settimeout(10)  # 确保有足够时间接收所有传感器数据
            
            # 接收数据
            all_data = b''
            start_time = time.time()
            timeout_seconds = 10
            
            # 持续接收数据，直到超时或收集到足够的数据包
            while time.time() - start_time < timeout_seconds:
                try:
                    chunk = self.socket.recv(1024)
                    if not chunk:
                        break
                    all_data += chunk
                    
                    # 更新最后通信时间
                    self.last_communication_time = datetime.datetime.now().isoformat()
                    
                    # 检查是否已经收集到足够的数据包
                    if len(all_data) >= 9 * 6:  # 假设需要6个传感器数据包，每个9字节
                        break
                except socket.timeout:
                    break
            
            if not all_data:
                logger.error("未接收到任何传感器数据")
                return {}
                
            # 只在DEBUG级别打印原始数据
            if logger.getEffectiveLevel() <= logging.DEBUG:
                hex_data = ' '.join([f'{b:02X}' for b in all_data])
                logger.debug(f"接收到传感器原始数据: {hex_data}")
            
            # 解析接收到的数据
            result = self._parse_sensor_data(all_data)
            
            # 以简洁的方式记录关键信息
            logger.info(f"已获取传感器数据: {len(all_data)} 字节")
            
            return result
                
        except socket.timeout:
            logger.error("获取传感器数据超时，没有收到响应")
            return {}
        except Exception as e:
            logger.error(f"获取传感器数据失败: {str(e)}")
            self.connected = False  # 标记为断开连接，下次操作时将尝试重连
            return {}
        
    def _parse_sensor_data(self, data: bytes) -> Dict[str, float]:
        """解析WSN传感器数据"""
        result = {
            'air_temperature': 0.0,
            'air_humidity': 0.0,
            'soil_temperature': 0.0,
            'soil_moisture': 0.0,
            'light_intensity': 0.0,
            'co2_concentration': 0.0
        }
        
        # 记录数据包解析情况，用于调试
        found_data_types = set()
        
        try:
            # 查找数据包
            i = 0
            while i <= len(data) - 9:  # 每个数据包长度为9字节
                # 检查数据包头尾标识 (0xB5...0x5B)
                if data[i] == 0xB5 and data[i+8] == 0x5B:
                    # 提取设备类型
                    device_type = data[i+1]
                    device_addr = data[i+2]
                    device_data = data[i+3:i+8]
                    
                    # 记录发现的传感器类型
                    found_data_types.add(device_type)
                    
                    # 降低日志级别，详细解析信息只在DEBUG级别输出
                    logger.debug(f"解析到设备数据包: 类型={hex(device_type)}, 地址={hex(device_addr)}")
                    
                    # 根据kv_wsn虚拟平台的协议进行解析
                    if device_type == 0x31:  # 空气温湿度传感器
                        try:
                            air_temp = round(int.from_bytes(device_data[:2], byteorder='big', signed=False) / 100.0, 1)
                            air_humi = round(int.from_bytes(device_data[2:4], byteorder='big', signed=False) / 100.0, 1)
                            
                            result['air_temperature'] = air_temp
                            result['air_humidity'] = air_humi
                        except Exception as e:
                            logger.error(f"空气温湿度解析错误: {str(e)}")
                            
                    elif device_type == 0x32:  # 土壤温湿度传感器
                        try:
                            soil_temp = round(int.from_bytes(device_data[:2], byteorder='big', signed=False) / 100.0, 1)
                            soil_humi = round(int.from_bytes(device_data[2:4], byteorder='big', signed=False) / 100.0, 1)
                            
                            result['soil_temperature'] = soil_temp
                            result['soil_moisture'] = soil_humi
                        except Exception as e:
                            logger.error(f"土壤温湿度解析错误: {str(e)}")
                        
                    elif device_type == 0x33:  # CO2浓度
                        try:
                            co2 = int.from_bytes(device_data[:2], byteorder='big', signed=False)
                            result['co2_concentration'] = co2
                        except Exception as e:
                            logger.error(f"CO2浓度解析错误: {str(e)}")
                        
                    elif device_type == 0x34:  # 光照度
                        try:
                            light = int.from_bytes(device_data[:2], byteorder='big', signed=False)
                            result['light_intensity'] = light
                        except Exception as e:
                            logger.error(f"光照度解析错误: {str(e)}")

                i += 9  # 移动到下一个可能的数据包
            
            # 记录找到的所有传感器类型，只在DEBUG级别输出
            logger.debug(f"找到的传感器类型: {[hex(t) for t in found_data_types]}")
            
            # 重要的结果数据保留在INFO级别
            logger.info(f"传感器数据解析完成: 温度={result['air_temperature']}°C, 湿度={result['air_humidity']}%, 光照={result['light_intensity']}lux, CO2={result['co2_concentration']}ppm")
            
            # 检查是否缺少某些传感器数据
            missing_sensors = []
            for key, value in result.items():
                if value == 0.0:
                    missing_sensors.append(key)
                
            if missing_sensors:
                logger.warning(f"缺少传感器数据: {', '.join(missing_sensors)}")
            
            return result
            
        except Exception as e:
            logger.error(f"解析传感器数据失败: {str(e)}")
            return result  # 返回默认值
            
    def get_relay_status(self, response: bytes) -> Optional[list]:
        """解析继电器状态响应
        
        按照kv_wsn虚拟平台协议解析继电器状态
        协议格式: A5 20 addr status1 status2 status3 status4 FF 5A
        """
        try:
            # 检查是否是继电器协议响应 (A5...5A)
            if len(response) >= 8 and response[0] == 0xA5 and response[-1] == 0x5A:
                # kv_wsn虚拟平台的协议中，状态位于字节3-6
                # 协议格式: A5 20 addr status1 status2 status3 status4 FF 5A
                status = []
                for i in range(4):
                    # 确保索引不超出范围
                    if i + 3 < len(response):
                        # 检查字节3-6的值，1表示开启，0表示关闭
                        status.append(response[i + 3] == 1)
                    else:
                        # 如果数据不完整，假设该通道关闭
                        status.append(False)
                
                # 确保返回长度为4的列表
                while len(status) < 4:
                    status.append(False)
                    
                logger.info(f"解析到继电器状态: {status}")
                return status
                
            # 如果是传感器数据格式 (B5...5B)
            elif len(response) >= 9 and response[0] == 0xB5 and response[8] == 0x5B:
                # 传感器数据，不包含继电器状态
                logger.warning("接收到传感器数据，不包含继电器状态")
                return [False, False, False, False]  # 默认所有通道关闭
            else:
                logger.warning(f"未知的响应格式: {' '.join([f'{b:02X}' for b in response])}")
                return [False, False, False, False]  # 默认所有通道关闭
        except Exception as e:
            logger.error(f"解析继电器状态失败: {str(e)}")
            return [False, False, False, False]  # 默认所有通道关闭

    def make_relay_command(self, device_id: int, status: list) -> Optional[bytearray]:
        """生成继电器控制命令
        
        按照kv_wsn库的格式生成继电器命令
        命令格式: A5 20 address status1 status2 status3 status4 FF 5A
        """
        try:
            if len(status) != 4:
                logger.error(f"继电器状态列表长度错误: {len(status)}，应为4")
                return None
                
            # 按照原始kv_wsn格式构建命令
            # A5 + 设备类型(0x20=继电器) + 地址 + 4个通道状态 + FF + 5A
            command = bytearray([0xA5, 0x20, device_id & 0xFF])
            
            # 将状态值转换为字节，确保值为0或1
            for i in range(4):
                # 明确转换为整数0或1，避免任何其他值
                status_value = 1 if status[i] else 0
                command.append(status_value)
                
            # 添加保留字节和结束标志
            command.append(0xFF)
            command.append(0x5A)
            
            # 打印完整的命令字节
            cmd_str = ' '.join([f'{b:02X}' for b in command])
            logger.info(f"生成继电器命令: {cmd_str}")
            
            return command
        except Exception as e:
            logger.error(f"生成继电器命令失败: {str(e)}")
            return None

    def ping(self) -> bool:
        """
        发送ping命令测试连接状态
        
        Returns:
            bool: 连接是否正常
        """
        if not self.socket:
            logger.error("WSN客户端未初始化")
            self.connected = False
            return False
            
        try:
            logger.info("发送Ping命令测试通信")
            
            # 构建ping命令：A5 00 00 FF FF FF FF FF 5A
            ping_cmd = bytearray([0xA5, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x5A])
            
            # 发送命令
            self.socket.send(ping_cmd)
            
            # 更新最后通信时间
            self.last_communication_time = datetime.datetime.now().isoformat()
            
            # 设置较短的超时时间
            self.socket.settimeout(2)
            
            try:
                # 接收响应
                response = self.socket.recv(1024)
                
                # 更新最后通信时间
                self.last_communication_time = datetime.datetime.now().isoformat()
                
                # 如果收到响应，表示连接正常
                if response and len(response) > 0:
                    logger.info("Ping测试成功，连接正常")
                    self.connected = True
                    return True
                else:
                    logger.warning("Ping测试失败，未收到响应")
                    self.connected = False
                    return False
            except socket.timeout:
                logger.warning("Ping测试超时")
                self.connected = False
                return False
        except Exception as e:
            logger.error(f"Ping测试失败: {str(e)}")
            self.connected = False
            return False