import request from '@/utils/request'

// 获取设备列表
export function getDeviceList() {
  return request({
    url: '/api/device/devices',
    method: 'get'
  })
}

// 获取设备详情
export function getDeviceDetail(id) {
  return request({
    url: `/api/device/devices/${id}`,
    method: 'get'
  })
}

// 控制设备
export function controlDevice(deviceType, action) {
  return request({
    url: '/api/device/control',
    method: 'post',
    data: {
      device_type: deviceType,
      action
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

// 获取阈值设置
export function getThresholds() {
  return request({
    url: '/api/thresholds',
    method: 'get'
  })
}

// 更新阈值设置
export function updateThresholds(data) {
  return request({
    url: '/api/thresholds',
    method: 'post',
    data
  })
}

// 开启/关闭智能控制
export function toggleSmartControl(enabled) {
  return request({
    url: '/api/smart-control',
    method: 'post',
    data: { enabled }
  })
}

// 连接设备
export function connectDevice(ip, port) {
  return request({
    url: '/api/connect',
    method: 'post',
    data: { ip, port }
  })
}

// 断开设备连接
export function disconnectDevice() {
  return request({
    url: '/api/disconnect',
    method: 'post'
  })
}

// 获取设备操作历史
export function getDeviceHistory(deviceId, params) {
  return request({
    url: `/api/device/${deviceId}/history`,
    method: 'get',
    params
  })
}

// 更新设备配置
export function updateDeviceConfig(deviceId, config) {
  return request({
    url: `/api/devices/${deviceId}/config`,
    method: 'put',
    data: config
  })
}

// 添加新设备
export function addDevice(data) {
  return request({
    url: '/api/devices',
    method: 'post',
    data
  })
}

// 删除设备
export function deleteDevice(deviceId) {
  return request({
    url: `/api/devices/${deviceId}`,
    method: 'delete'
  })
}

// 控制继电器
export function controlRelay(deviceType, action) {
  return request({
    url: '/api/device/control',
    method: 'post',
    data: {
      device_type: deviceType,
      action: action
    }
  })
}

// 默认设备列表数据
export const defaultDevices = [
  {
    id: 1,
    name: '外通风',
    type: 'external_fan',
    status: 'inactive',
    description: '控制温室外部通风系统',
    last_active: null
  },
  {
    id: 2,
    name: '内通风',
    type: 'internal_fan',
    status: 'inactive',
    description: '控制温室内部通风系统',
    last_active: null
  },
  {
    id: 3,
    name: '天窗',
    type: 'skylight',
    status: 'inactive',
    description: '控制温室顶部天窗',
    last_active: null
  },
  {
    id: 4,
    name: '喷灌',
    type: 'spray',
    status: 'inactive',
    description: '控制温室喷灌系统',
    last_active: null
  },
  {
    id: 5,
    name: '水帘',
    type: 'water_curtain',
    status: 'inactive',
    description: '控制温室水帘系统',
    last_active: null
  }
] 