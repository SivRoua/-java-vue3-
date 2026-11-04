/**
 * 数据处理助手工具
 * 提供安全的数据处理方法，防止常见的数据类型错误
 */

/**
 * 确保数据是数组形式
 * @param {any} data 需要检查的数据
 * @returns {Array} 转换后的数组
 */
export function ensureArray(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  
  // 处理嵌套数据结构
  if (data.data && Array.isArray(data.data)) return data.data;
  if (data.items && Array.isArray(data.items)) return data.items;
  if (data.records && Array.isArray(data.records)) return data.records;
  if (data.results && Array.isArray(data.results)) return data.results;
  
  // 如果是单个对象，包装为数组
  if (typeof data === 'object') {
    // 检查是否包含传感器数据相关字段
    const hasSensorFields = data.timestamp || 
                          data.air_temperature !== undefined || 
                          data.air_humidity !== undefined || 
                          data.soil_moisture !== undefined || 
                          data.soil_temperature !== undefined || 
                          data.light_intensity !== undefined || 
                          data.temperature !== undefined || 
                          data.humidity !== undefined;
                          
    if (hasSensorFields) {
      return [data];
    }
  }
  
  // 尝试转换其他类型
  try {
    // 如果是JSON字符串，尝试解析
    if (typeof data === 'string' && (data.startsWith('[') || data.startsWith('{'))) {
      const parsed = JSON.parse(data);
      return ensureArray(parsed); // 递归处理解析结果
    }
  } catch (e) {
    console.warn('将数据转换为数组失败:', e);
  }
  
  return Array.isArray(data) ? data : [];
}

/**
 * 安全地解析浮点数
 * @param {any} value 需要解析的值
 * @param {number} defaultValue 默认值，当解析失败时返回
 * @returns {number} 解析后的浮点数
 */
export function safeParseFloat(value, defaultValue = 0) {
  if (value === undefined || value === null) return defaultValue;
  
  // 处理特殊的字符串格式
  if (typeof value === 'string') {
    // 移除非数字字符（保留小数点和负号）
    value = value.replace(/[^0-9.-]/g, '');
    // 处理多个小数点的情况
    const parts = value.split('.');
    if (parts.length > 2) {
      value = parts[0] + '.' + parts.slice(1).join('');
    }
  }
  
  const parsed = parseFloat(value);
  return isNaN(parsed) ? defaultValue : parsed;
}

/**
 * 安全地解析整数
 * @param {any} value 需要解析的值
 * @param {number} defaultValue 默认值，当解析失败时返回
 * @returns {number} 解析后的整数
 */
export function safeParseInt(value, defaultValue = 0) {
  if (value === undefined || value === null) return defaultValue;
  const parsed = parseInt(value);
  return isNaN(parsed) ? defaultValue : parsed;
}

/**
 * 安全地获取对象属性
 * @param {Object} obj 目标对象
 * @param {string} path 属性路径，如 'user.profile.name'
 * @param {any} defaultValue 默认值，当属性不存在时返回
 * @returns {any} 属性值或默认值
 */
export function safeGet(obj, path, defaultValue = undefined) {
  if (!obj || typeof obj !== 'object') return defaultValue;
  
  const keys = path.split('.');
  let result = obj;
  
  for (const key of keys) {
    if (result === undefined || result === null || typeof result !== 'object') {
      return defaultValue;
    }
    result = result[key];
  }
  
  return result === undefined ? defaultValue : result;
}

/**
 * 安全地进行数组操作，确保方法存在且目标是数组
 * @param {Array} arr 目标数组
 * @param {string} method 数组方法名，如 'map', 'filter', 'reduce'
 * @param {Function} callback 回调函数
 * @param {any} initialValue 初始值，用于reduce方法
 * @returns {any} 方法执行结果
 */
export function safeArrayOperation(arr, method, callback, initialValue) {
  // 确保是数组
  const safeArr = ensureArray(arr);
  
  // 如果是空数组并且是reduce方法，直接返回初始值
  if (safeArr.length === 0 && method === 'reduce') {
    return initialValue;
  }
  
  // 执行数组方法
  switch (method) {
    case 'map':
      return safeArr.map(callback);
    case 'filter':
      return safeArr.filter(callback);
    case 'reduce':
      return safeArr.reduce(callback, initialValue);
    case 'forEach':
      return safeArr.forEach(callback);
    case 'some':
      return safeArr.some(callback);
    case 'every':
      return safeArr.every(callback);
    case 'find':
      return safeArr.find(callback);
    case 'findIndex':
      return safeArr.findIndex(callback);
    default:
      console.warn(`未支持的数组方法: ${method}`);
      return safeArr;
  }
}

/**
 * 规范化传感器数据，处理多种可能的属性名
 * @param {Object} data 传感器数据对象
 * @returns {Object} 规范化后的数据对象
 */
export function normalizeSensorData(data) {
  if (!data || typeof data !== 'object') {
    return {
      temperature: 0,
      humidity: 0,
      soil_temperature: 0,
      soil_moisture: 0,
      light_intensity: 0,
      co2_level: 0
    };
  }
  
  return {
    // 温度
    temperature: safeParseFloat(data.air_temperature || data.temperature),
    // 湿度
    humidity: safeParseFloat(data.air_humidity || data.humidity),
    // 土壤温度
    soil_temperature: safeParseFloat(data.soil_temperature),
    // 土壤湿度
    soil_moisture: safeParseFloat(data.soil_moisture),
    // 光照强度
    light_intensity: safeParseFloat(data.light_intensity),
    // CO2浓度
    co2_level: safeParseFloat(data.co2_concentration || data.co2_level),
    // 原始时间戳
    timestamp: data.timestamp
  };
}

export default {
  ensureArray,
  safeParseFloat,
  safeParseInt,
  safeGet,
  safeArrayOperation,
  normalizeSensorData
}; 