/**
 * 通用工具函数
 */
import defaultAvatar from '@/assets/avator.png'

/**
 * 获取格式化的头像URL
 * @param {string} avatar 用户头像URL
 * @returns {string} 格式化后的头像URL
 */
export function getAvatarUrl(avatar) {
  if (!avatar) {
    return defaultAvatar;
  }
  
  // 如果已经是绝对URL或数据URL，直接返回
  if (avatar.startsWith('http') || avatar.startsWith('data:')) {
    return avatar;
  }
  
  // 如果是相对路径，转换为绝对路径
  if (avatar.startsWith('/')) {
    // 移除开头的斜杠
    avatar = avatar.substring(1);
  }
  
  try {
    // 动态导入图像
    return new URL(`../assets/${avatar}`, import.meta.url).href;
  } catch (error) {
    console.error('加载头像出错:', error);
    return defaultAvatar;
  }
}

/**
 * 确保对象的安全访问
 * @param {Object} obj 对象
 * @param {string} path 属性路径，如 'user.profile.name'
 * @param {*} defaultValue 默认值
 * @returns {*} 属性值或默认值
 */
export function safeGet(obj, path, defaultValue = undefined) {
  if (!obj || !path) return defaultValue;
  
  const keys = path.split('.');
  let result = obj;
  
  for (const key of keys) {
    if (result === null || result === undefined || typeof result !== 'object') {
      return defaultValue;
    }
    result = result[key];
  }
  
  return result === undefined ? defaultValue : result;
}

/**
 * 安全地解析JSON
 * @param {string} str JSON字符串
 * @param {Object} fallback 解析失败时的默认值
 * @returns {Object} 解析结果或默认值
 */
export function safeJSONParse(str, fallback = {}) {
  if (!str) return fallback;
  try {
    return JSON.parse(str);
  } catch (e) {
    console.error('JSON解析错误:', e);
    return fallback;
  }
}

/**
 * 防抖函数
 * @param {Function} fn 要执行的函数
 * @param {number} delay 延迟时间（毫秒）
 * @returns {Function} 防抖处理后的函数
 */
export function debounce(fn, delay = 300) {
  let timer = null;
  return function(...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
}

export default {
  getAvatarUrl,
  safeGet,
  safeJSONParse,
  debounce
} 