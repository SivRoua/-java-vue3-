import request from '@/utils/request'

// 获取自动控制状态
export function getAutoControlStatus() {
  return request({
    url: '/api/auto-control/status',
    method: 'get'
  }).then(response => {
    return {
      enabled: response.enabled || false,
      thresholds: response.thresholds || {},
      message: response.message || '获取状态成功'
    }
  }).catch(error => {
    console.error('获取自动控制状态失败:', error)
    return {
      enabled: false,
      thresholds: {},
      error: error.message || '获取状态失败'
    }
  })
}

// 启用自动控制
export function enableAutoControl() {
  return request({
    url: '/api/auto-control/enable',
    method: 'post'
  }).then(response => {
    return {
      success: true,
      enabled: response.enabled,
      message: response.message || '自动控制已启用'
    }
  }).catch(error => {
    console.error('启用自动控制失败:', error)
    return {
      success: false,
      enabled: false,
      error: error.message || '启用失败'
    }
  })
}

// 禁用自动控制
export function disableAutoControl() {
  return request({
    url: '/api/auto-control/disable',
    method: 'post'
  }).then(response => {
    return {
      success: true,
      enabled: false,
      message: response.message || '自动控制已禁用'
    }
  }).catch(error => {
    console.error('禁用自动控制失败:', error)
    return {
      success: false,
      enabled: true,
      error: error.message || '禁用失败'
    }
  })
}// 获取阈值设置
export function getThresholds() {
  return request({
    url: '/api/auto-control/thresholds',
    method: 'get'
  }).then(response => {
    return {
      success: true,
      thresholds: response || {}
    }
  }).catch(error => {
    console.error('获取阈值设置失败:', error)
    return {
      success: false,
      thresholds: {},
      error: error.message || '获取阈值失败'
    }
  })
}

// 更新阈值设置
export function updateThresholds(thresholds) {
  return request({
    url: '/api/auto-control/thresholds',
    method: 'post',
    data: thresholds
  }).then(response => {
    return {
      success: true,
      thresholds: response.thresholds || {},
      message: response.message || '阈值设置已更新'
    }
  }).catch(error => {
    console.error('更新阈值设置失败:', error)
    return {
      success: false,
      error: error.message || '更新阈值失败'
    }
  })
}