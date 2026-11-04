<template>
  <div class="auto-control-page">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span>智能农业自动控制系统</span>
          <el-button type="primary" size="small" @click="refreshData">
            <i class="el-icon-refresh"></i> 刷新
          </el-button>
        </div>
      </template>
      
      <div class="page-content">
        <el-row :gutter="20">
          <el-col :span="16">
            <auto-control-panel ref="controlPanel" />
          </el-col>
          
          <el-col :span="8">
            <el-card class="info-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>系统信息</span>
                </div>
              </template>
              <div class="info-content">
                <div class="info-item">
                  <span class="label">设备连接状态:</span>
                  <el-tag :type="connectionStatus ? 'success' : 'danger'">
                    {{ connectionStatus ? '已连接' : '未连接' }}
                  </el-tag>
                </div>
                
                <div class="info-item">
                  <span class="label">自动控制状态:</span>
                  <el-tag :type="autoControlEnabled ? 'success' : 'info'">
                    {{ autoControlEnabled ? '已启用' : '已禁用' }}
                  </el-tag>
                </div>
                
                <el-divider></el-divider>
                
                <div class="info-item">
                  <span class="label">最后更新时间:</span>
                  <span>{{ lastUpdateTime }}</span>
                </div>
                
                <div class="info-item">
                  <span class="label">当前传感器数据:</span>
                </div>
                
                <div class="sensor-data">
                  <div class="sensor-item" v-for="(value, key) in sensorData" :key="key">
                    <span class="sensor-label">{{ getSensorLabel(key) }}:</span>
                    <span class="sensor-value">{{ value }}{{ getSensorUnit(key) }}</span>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template><script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import AutoControlPanel from '@/components/AutoControlPanel.vue'
import { getConnectionStatus } from '@/api/device'
import { getSensorData } from '@/api/device'
import { getAutoControlStatus } from '@/api/auto-control'

const controlPanel = ref(null)
const connectionStatus = ref(false)
const autoControlEnabled = ref(false)
const lastUpdateTime = ref('--')
const updateInterval = ref(null)
const sensorData = ref({
  air_temperature: 0,
  air_humidity: 0,
  soil_temperature: 0,
  soil_moisture: 0,
  light_intensity: 0,
  co2_concentration: 0
})

// 刷新数据
const refreshData = async () => {
  try {
    // 获取连接状态
    const connRes = await getConnectionStatus()
    connectionStatus.value = connRes.status === 'connected'
    
    // 获取传感器数据
    const sensorRes = await getSensorData()
    if (sensorRes.data) {
      sensorData.value = sensorRes.data
    }
    
    // 获取自动控制状态
    const autoControlRes = await getAutoControlStatus()
    autoControlEnabled.value = autoControlRes.enabled
    
    // 更新时间
    lastUpdateTime.value = new Date().toLocaleString()
    
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('刷新数据失败')
  }
}

// 获取传感器标签
const getSensorLabel = (key) => {
  const labels = {
    air_temperature: '空气温度',
    air_humidity: '空气湿度',
    soil_temperature: '土壤温度',
    soil_moisture: '土壤湿度',
    light_intensity: '光照强度',
    co2_concentration: 'CO2浓度'
  }
  return labels[key] || key
}// 获取传感器单位
const getSensorUnit = (key) => {
  const units = {
    air_temperature: '°C',
    air_humidity: '%',
    soil_temperature: '°C',
    soil_moisture: '%',
    light_intensity: 'lux',
    co2_concentration: 'ppm'
  }
  return units[key] || ''
}

onMounted(async () => {
  // 初始加载数据
  await refreshData()
  
  // 设置定时刷新 (每10秒)
  updateInterval.value = setInterval(refreshData, 10000)
})

onUnmounted(() => {
  // 清除定时器
  if (updateInterval.value) {
    clearInterval(updateInterval.value)
  }
})
</script>

<style scoped>
.auto-control-page {
  padding: 20px;
}

.page-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-content {
  margin-top: 10px;
}

.info-card {
  height: 100%;
}

.info-content {
  padding: 10px 0;
}

.info-item {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.label {
  font-weight: bold;
  margin-right: 10px;
  color: #606266;
}

.sensor-data {
  margin-top: 10px;
  border-top: 1px dashed #ebeef5;
  padding-top: 10px;
}

.sensor-item {
  margin-bottom: 5px;
  display: flex;
  justify-content: space-between;
  padding: 5px 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.sensor-label {
  color: #606266;
}

.sensor-value {
  font-weight: bold;
  color: #409eff;
}
</style>