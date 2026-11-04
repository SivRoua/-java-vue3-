import { defineStore } from 'pinia'
import { getDeviceList as getDevices, controlDevice, getDeviceHistory } from '@/api/control'
import { getConnectionStatus } from '@/api/device'
import { ElMessage } from 'element-plus'

export const useControlStore = defineStore('control', {
  state: () => ({
    devices: [],
    deviceHistory: {},
    controlStatus: {},
    loading: false,
    connection: {
      isConnected: false,
      message: '未连接',
      host: '',
      port: 0,
      lastHeartbeat: null,
      lastChecked: null
    }
  }),

  getters: {
    getDeviceById: (state) => (id) => state.devices.find(d => d.id === id),
    getDeviceHistory: (state) => (id) => state.deviceHistory[id] || [],
    isDeviceOnline: (state) => (id) => {
      const device = state.devices.find(d => d.id === id)
      return device?.status === 'active'
    },
    connectionStatus: (state) => state.connection
  },

  actions: {
    // 更新连接状态
    updateConnectionStatus(connectionData) {
      this.connection = {
        ...this.connection,
        ...connectionData,
        lastChecked: new Date().toISOString()
      }
    },

    // 获取最新连接状态
    async refreshConnectionStatus() {
      try {
        const response = await getConnectionStatus()
        
        this.updateConnectionStatus({
          isConnected: response.status === 'connected',
          message: response.message || (response.status === 'connected' ? '设备已连接' : '设备未连接'),
          host: response.host,
          port: response.port,
          lastHeartbeat: response.last_heartbeat
        })
        
        return this.connection
      } catch (error) {
        console.error('刷新连接状态失败:', error)
        
        this.updateConnectionStatus({
          isConnected: false,
          message: '获取连接状态失败'
        })
        
        return this.connection
      }
    },

    async fetchDevices() {
      try {
        const { data } = await getDevices()
        this.devices = data
        return data
      } catch (error) {
        ElMessage.error(error.message || '获取设备列表失败')
        return null
      }
    },

    async controlDevice(deviceType, action) {
      this.loading = true
      try {
        // 先检查连接状态
        await this.refreshConnectionStatus()
        
        if (!this.connection.isConnected) {
          throw new Error('设备未连接，无法控制')
        }
        
        const { data } = await controlDevice(deviceType, action)
        // 更新设备状态
        const index = this.devices.findIndex(d => d.type === deviceType)
        if (index !== -1) {
          this.devices[index] = { 
            ...this.devices[index], 
            status: action === 'open' ? 'active' : 'inactive',
            last_active: new Date().toISOString()
          }
        }
        this.controlStatus[deviceType] = { action, status: 'success', timestamp: new Date() }
        return data
      } catch (error) {
        this.controlStatus[deviceType] = { action, status: 'failed', timestamp: new Date(), error: error.message }
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchDeviceHistory(deviceId, params) {
      try {
        const { data } = await getDeviceHistory(deviceId, params)
        this.deviceHistory[deviceId] = data
        return data
      } catch (error) {
        ElMessage.error(error.message || '获取设备历史记录失败')
        return null
      }
    },

    // 清除设备历史记录
    clearDeviceHistory(deviceId) {
      if (deviceId) {
        delete this.deviceHistory[deviceId]
      } else {
        this.deviceHistory = {}
      }
    },

    // 重置状态
    resetState() {
      this.devices = []
      this.deviceHistory = {}
      this.controlStatus = {}
      this.loading = false
      this.connection = {
        isConnected: false,
        message: '未连接',
        host: '',
        port: 0,
        lastHeartbeat: null,
        lastChecked: null
      }
    }
  }
}) 