import request from '@/utils/request'

/**
 * 获取所有警报规则
 * @returns {Promise} 包含警报规则列表的Promise
 */
export function getAlertRules() {
  return request({
    url: '/api/alerts/rules',
    method: 'get'
  })
}

/**
 * 获取单个警报规则
 * @param {number} id 警报规则ID
 * @returns {Promise} 包含警报规则的Promise
 */
export function getAlertRule(id) {
  return request({
    url: `/api/alerts/rules/${id}`,
    method: 'get'
  })
}

/**
 * 创建警报规则
 * @param {Object} data 警报规则数据
 * @returns {Promise} 创建结果的Promise
 */
export function createAlertRule(data) {
  return request({
    url: '/api/alerts/rules',
    method: 'post',
    data
  })
}

/**
 * 更新警报规则
 * @param {number} id 警报规则ID
 * @param {Object} data 警报规则数据
 * @returns {Promise} 更新结果的Promise
 */
export function updateAlertRule(id, data) {
  return request({
    url: `/api/alerts/rules/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除警报规则
 * @param {number} id 警报规则ID
 * @returns {Promise} 删除结果的Promise
 */
export function deleteAlertRule(id) {
  return request({
    url: `/api/alerts/rules/${id}`,
    method: 'delete'
  })
}

/**
 * 切换警报规则启用状态
 * @param {number} id 警报规则ID
 * @returns {Promise} 切换结果的Promise
 */
export function toggleAlertRule(id) {
  return request({
    url: `/api/alerts/rules/${id}/toggle`,
    method: 'put'
  })
}

/**
 * 获取最近的警报记录
 * @param {number} limit 记录数量限制
 * @returns {Promise} 包含警报记录的Promise
 */
export function getRecentAlerts(limit = 10) {
  return request({
    url: '/api/alerts/recent',
    method: 'get',
    params: { limit }
  })
}

/**
 * 标记警报为已处理
 * @param {number} id 警报ID
 * @returns {Promise} 处理结果的Promise
 */
export function handleAlert(id) {
  return request({
    url: `/api/alerts/handle/${id}`,
    method: 'put'
  })
}

/**
 * 获取未处理警报数量
 * @returns {Promise} 包含警报数量的Promise
 */
export function getAlertCount() {
  return request({
    url: '/api/alerts/count',
    method: 'get'
  })
}

/**
 * 获取自动控制规则
 * @returns {Promise} 包含自动控制规则的Promise
 */
export function getAutoControlRules() {
  return request({
    url: '/api/alerts/auto-control/rules',
    method: 'get'
  })
}

/**
 * 获取自动控制日志
 * @param {number} limit 记录数量限制
 * @returns {Promise} 包含自动控制日志的Promise
 */
export function getAutoControlLogs(limit = 10) {
  return request({
    url: '/api/alerts/auto-control/logs',
    method: 'get',
    params: { limit }
  })
}

// 导出警报API对象
export const alertsApi = {
  getAlertRules,
  getAlertRule,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule,
  toggleAlertRule,
  getRecentAlerts,
  handleAlert,
  getAlertCount,
  getAutoControlRules,
  getAutoControlLogs
} 