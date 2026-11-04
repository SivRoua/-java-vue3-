import request from '@/utils/request'
import axios from 'axios'

// 获取传感器数据
export function getSensorData() {
  return new Promise(async (resolve, reject) => {
    try {
      // 首先尝试使用request工具
      const response = await request({
        url: '/api/sensor-data',
        method: 'get',
        noErrorNotification: true,
        timeout: 10000
      });
      resolve(response);
    } catch (error) {
      console.log('通过request获取传感器数据失败，尝试直接使用axios:', error);
      
      // 如果失败，尝试直接使用axios
      try {
        const directResponse = await axios.get('http://localhost:5000/api/sensor-data', {
          timeout: 10000
        });
        resolve(directResponse.data);
      } catch (directError) {
        console.log('直接使用axios获取传感器数据也失败:', directError);
        
        // 最后尝试使用备用接口
        try {
          const backupResponse = await axios.get('/api/sensor-data', {
            timeout: 10000
          });
          resolve(backupResponse.data);
        } catch (backupError) {
          console.error('所有尝试均失败:', backupError);
          reject(backupError);
        }
      }
    }
  });
}

// 获取实时传感器数据（无论设备连接状态如何）
export function getRealtimeSensorData() {
  return request({
    url: '/api/device/public/sensor-data',
    method: 'get',
    noErrorNotification: true, // 即使有错误也不显示通知
    timeout: 10000 // 增加超时时间
  })
}

// 处理传感器数据响应
export function processSensorDataResponse(response) {
  // 检查响应格式
  if (response && response.data) {
    // 新格式响应
    const data = response.data;
    const source = response.source || 'unknown';
    const timestamp = response.timestamp;
    const connectionError = response.connection_error;
    
    // 返回处理后的数据
    return {
      data,
      source,
      timestamp,
      connectionError,
      isRealtime: source === 'realtime'
    };
  } else if (response && typeof response === 'object') {
    // 旧格式响应，直接返回
    return {
      data: response,
      source: 'legacy',
      timestamp: new Date().toISOString(),
      connectionError: null,
      isRealtime: true
    };
  }
  
  // 无效响应
  return {
    data: null,
    source: 'error',
    timestamp: new Date().toISOString(),
    connectionError: '无效的数据格式',
    isRealtime: false
  };
}

// 获取传感器历史数据
export function getSensorHistory(params) {
  return request({
    url: '/api/sensor-history',
    method: 'get',
    params
  })
}

// 控制设备
export function controlDevice(deviceType, action) {
  return request({
    url: '/api/device/control',
    method: 'post',
    data: {
      device_type: deviceType,
      action: action
    }
  })
}

// 获取设备状态
export function getDeviceStatus() {
  return request({
    url: '/api/device/status',
    method: 'get'
  })
} 