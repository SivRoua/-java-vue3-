import request from '@/utils/request'
import axios from 'axios'

// 创建一个简单的数据缓存系统
const dataCache = {
  historyData: {
    data: null,
    timestamp: null,
    expirationTime: 5 * 60 * 1000 // 5分钟缓存过期
  },
  statistics: {
    data: null,
    timestamp: null, 
    expirationTime: 5 * 60 * 1000
  }
}

// 检查缓存是否有效
function isCacheValid(cacheKey) {
  const cache = dataCache[cacheKey]
  return cache && 
         cache.data && 
         cache.timestamp && 
         (Date.now() - cache.timestamp < cache.expirationTime)
}

// 更新缓存
function updateCache(cacheKey, data) {
  if (dataCache[cacheKey]) {
    dataCache[cacheKey].data = data
    dataCache[cacheKey].timestamp = Date.now()
  }
}

// 安全地处理响应数据
function safelyProcessResponse(response) {
  if (!response) return [];
  
  // 如果已经是数组，直接返回
  if (Array.isArray(response)) {
    return response;
  }
  
  // 处理常见的API响应格式
  if (typeof response === 'object') {
    // 如果response.data是数组，返回它
    if (Array.isArray(response.data)) {
      return response.data;
    } 
    // 如果response.data.data是数组，返回它（嵌套结构）
    else if (response.data && Array.isArray(response.data.data)) {
      return response.data.data;
    }
    // 检查是否有结果或records属性
    else if (Array.isArray(response.results)) {
      return response.results;
    }
    else if (Array.isArray(response.records)) {
      return response.records;
    }
    // 如果没有数组属性但有items属性
    else if (Array.isArray(response.items)) {
      return response.items;
    }
    // 如果响应是对象但没有明确的数组字段，尝试将其转为单元素数组
    else if (response.timestamp || 
            response.air_temperature !== undefined || 
            response.air_humidity !== undefined || 
            response.soil_moisture !== undefined || 
            response.soil_temperature !== undefined ||
            response.light_intensity !== undefined) {
      return [response];
    }
  }
  
  // 尝试解析字符串
  if (typeof response === 'string') {
    try {
      const parsed = JSON.parse(response);
      return safelyProcessResponse(parsed); // 递归处理解析后的对象
    } catch (e) {
      // 静默错误处理
    }
  }
  
  return [];
}

// 生成缓存键
function generateCacheKey(params) {
  const sortedParams = Object.entries(params || {})
    .sort(([keyA], [keyB]) => keyA.localeCompare(keyB))
    .map(([key, value]) => `${key}=${value}`)
    .join('&')
  
  return sortedParams || 'default'
}

// 优化获取历史数据函数
export function getHistoryData(params = {}) {
  return new Promise(async (resolve, reject) => {
    try {
      // 确保参数格式正确
      const safeParams = { ...params };
      
      // 如果没有提供日期参数，默认获取最近24小时的数据
      if (!safeParams.start_date) {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24); // 24小时前
        safeParams.start_date = start.toISOString();
        safeParams.end_date = end.toISOString();
      }
      
      // 处理日期格式，确保前后端日期格式一致
      if (safeParams.start_date instanceof Date) {
        safeParams.start_date = safeParams.start_date.toISOString();
      }
      
      if (safeParams.end_date instanceof Date) {
        safeParams.end_date = safeParams.end_date.toISOString();
      }
      
      // 生成缓存键
      const cacheKey = 'historyData:' + generateCacheKey(safeParams)
      
      // 检查是否有缓存
      if (dataCache.historyData && dataCache.historyData.customKeys && dataCache.historyData.customKeys[cacheKey]) {
        const cachedData = dataCache.historyData.customKeys[cacheKey]
        if (cachedData.timestamp && (Date.now() - cachedData.timestamp < dataCache.historyData.expirationTime)) {
          // 返回缓存数据
          console.log('使用缓存的历史数据', cachedData.data.length + '条记录')
          return resolve(cachedData.data)
        }
      }
      
      console.log('获取历史数据，参数:', safeParams)
      
      // 首先尝试使用request工具
      try {
        const response = await request({
          url: '/api/history/data',
          method: 'get',
          params: safeParams,
          timeout: 15000 // 增加超时时间
        });
        
        // 确保响应是数组
        const responseData = safelyProcessResponse(response);
        console.log('成功获取历史数据', responseData.length + '条记录')
        
        // 更新缓存
        if (!dataCache.historyData.customKeys) {
          dataCache.historyData.customKeys = {}
        }
        
        dataCache.historyData.customKeys[cacheKey] = {
          data: responseData,
          timestamp: Date.now()
        }
        
        return resolve(responseData);
      } catch (error) {
        console.error('首选API调用失败，尝试备用方法', error)
        
        // 如果失败，尝试直接使用axios
        try {
          const directResponse = await axios.get('http://localhost:5000/api/history/data', {
            params: safeParams,
            timeout: 15000 // 增加超时时间
          });
          
          // 确保响应是数组
          const responseData = safelyProcessResponse(directResponse.data);
          console.log('使用直接方法获取历史数据成功', responseData.length + '条记录')
          
          // 更新缓存
          if (!dataCache.historyData.customKeys) {
            dataCache.historyData.customKeys = {}
          }
          
          dataCache.historyData.customKeys[cacheKey] = {
            data: responseData,
            timestamp: Date.now()
          }
          
          return resolve(responseData);
        } catch (directError) {
          console.error('直接API调用失败，尝试最后备用接口', directError)
          
          // 最后尝试使用备用接口
          try {
            const backupResponse = await axios.get('http://localhost:5000/api/history', {
              params: safeParams,
              timeout: 15000 // 增加超时时间
            });
            
            // 确保响应是数组
            const responseData = safelyProcessResponse(backupResponse.data);
            console.log('使用备用接口获取历史数据成功', responseData.length + '条记录')
            
            // 更新缓存
            if (!dataCache.historyData.customKeys) {
              dataCache.historyData.customKeys = {}
            }
            
            dataCache.historyData.customKeys[cacheKey] = {
              data: responseData,
              timestamp: Date.now()
            }
            
            return resolve(responseData);
          } catch (backupError) {
            console.error('所有API调用都失败', backupError)
            reject(backupError);
          }
        }
      }
    } catch (error) {
      console.error('获取历史数据过程中发生未处理的错误', error)
      reject(error);
    }
  });
}

// 获取统计数据 (使用兼容路径)
export function getStatistics(params) {
  return new Promise(async (resolve, reject) => {
    try {
      // 检查是否有缓存
      const cacheKey = 'statistics:' + generateCacheKey(params)
      
      // 检查是否有缓存
      if (dataCache.statistics && dataCache.statistics.customKeys && dataCache.statistics.customKeys[cacheKey]) {
        const cachedData = dataCache.statistics.customKeys[cacheKey]
        if (cachedData.timestamp && (Date.now() - cachedData.timestamp < dataCache.statistics.expirationTime)) {
          // 返回缓存数据
          return resolve(cachedData.data)
        }
      }
      
      const response = await request({
        url: '/api/history',
        method: 'get',
        params,
        timeout: 8000  // 减少超时时间
      });
      
      // 更新缓存
      if (!dataCache.statistics.customKeys) {
        dataCache.statistics.customKeys = {}
      }
      
      dataCache.statistics.customKeys[cacheKey] = {
        data: response,
        timestamp: Date.now()
      }
      
      resolve(response);
    } catch (error) {
      try {
        const directResponse = await axios.get('http://localhost:5000/api/history', {
          params,
          timeout: 8000  // 减少超时时间
        });
        
        // 更新缓存
        const cacheKey = 'statistics:' + generateCacheKey(params)
        if (!dataCache.statistics.customKeys) {
          dataCache.statistics.customKeys = {}
        }
        
        dataCache.statistics.customKeys[cacheKey] = {
          data: directResponse.data,
          timestamp: Date.now()
        }
        
        resolve(directResponse.data);
      } catch (directError) {
        reject(directError);
      }
    }
  });
}

// 导出数据
export function exportData(params) {
  return new Promise(async (resolve, reject) => {
    try {
      const response = await request({
        url: '/api/history/data',
        method: 'get',
        params,
        responseType: 'blob',
        timeout: 15000  // 增加超时时间，因为导出可能需要更长时间
      });
      resolve(response);
    } catch (error) {
      try {
        const directResponse = await axios.get('http://localhost:5000/api/history/data', {
          params,
          responseType: 'blob',
          timeout: 15000
        });
        resolve(directResponse.data);
      } catch (directError) {
        reject(directError);
      }
    }
  });
}

// 兼容getSensorHistory
export function getSensorHistory(params) {
  return getHistoryData(params);
}

// 清除缓存
export function clearCache() {
  console.log('清除API缓存')
  Object.keys(dataCache).forEach(key => {
    dataCache[key].data = null;
    dataCache[key].timestamp = null;
    if (dataCache[key].customKeys) {
      dataCache[key].customKeys = {};
    }
  });
}

export const historyApi = {
  getHistoryData,
  getStatistics,
  exportData,
  getSensorHistory,
  clearCache
} 