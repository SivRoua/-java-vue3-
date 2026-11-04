<template>
  <div class="environment-dashboard">
    <div class="data-source-info">
      <span class="data-source" :class="dataSource === 'realtime' ? 'realtime' : 'cached'">
        数据来源: {{ dataSource === 'realtime' ? '实时数据' : dataSource === 'database' ? '数据库缓存' : '默认值' }}
      </span>
      <span class="last-update">更新时间: {{ formatTime(lastUpdate) }}</span>
      <span v-if="connectionError" class="connection-error">
        <el-tooltip :content="connectionError">
          <el-icon><WarningFilled /></el-icon>
        </el-tooltip>
        连接错误
      </span>
    </div>
    
    <div class="dashboard-grid">
      <!-- 实时数据卡片 -->
      <div class="data-card" v-for="metric in metrics" :key="metric.id">
        <h3>{{ metric.name }}</h3>
        <div class="value">{{ metric.value }}{{ metric.unit }}</div>
        <div class="status" :class="metric.status">{{ metric.statusText }}</div>
      </div>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-container">
      <div class="chart-row">
        <sensor-chart
          title="温度趋势"
          :data="temperatureData"
          type="temperature"
        />
        <sensor-chart
          title="湿度趋势"
          :data="humidityData"
          type="humidity"
        />
      </div>
      <div class="chart-row">
        <sensor-chart
          title="土壤湿度趋势"
          :data="soilMoistureData"
          type="soil_moisture"
        />
        <sensor-chart
          title="光照强度趋势"
          :data="lightIntensityData"
          type="light_intensity"
        />
      </div>
    </div>
    
    <!-- 警报面板 -->
    <div class="alerts-panel">
      <h2>实时警报</h2>
      <div class="alert-list">
        <div v-for="alert in alerts" :key="alert.id" class="alert-item" :class="alert.severity">
          <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
          <span class="alert-message">{{ alert.message }}</span>
          <button @click="acknowledgeAlert(alert.id)" v-if="alert.status === 'triggered'">
            确认
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import SensorChart from './SensorChart.vue'
import { getRealtimeSensorData, processSensorDataResponse } from '@/api/sensor'
import { ElMessage } from 'element-plus'
import { WarningFilled } from '@element-plus/icons-vue'

const metrics = ref([
  { id: 1, name: '温度', value: 25.5, unit: '°C', status: 'normal', statusText: '正常' },
  { id: 2, name: '湿度', value: 60, unit: '%', status: 'normal', statusText: '正常' },
  { id: 3, name: '土壤湿度', value: 75, unit: '%', status: 'warning', statusText: '偏高' },
  { id: 4, name: '光照强度', value: 800, unit: 'lux', status: 'normal', statusText: '正常' },
  { id: 5, name: 'CO2浓度', value: 400, unit: 'ppm', status: 'normal', statusText: '正常' },
  { id: 6, name: 'pH值', value: 6.5, unit: '', status: 'normal', statusText: '正常' }
])

const alerts = ref([])
const temperatureData = ref([])
const humidityData = ref([])
const soilMoistureData = ref([])
const lightIntensityData = ref([])
const dataSource = ref('无数据')
const lastUpdate = ref(new Date())
const connectionError = ref(null)

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const acknowledgeAlert = async (alertId) => {
  try {
    await fetch(`/api/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    // 更新警报列表
    alerts.value = alerts.value.filter(alert => alert.id !== alertId)
  } catch (error) {
    console.error('Error acknowledging alert:', error)
  }
}

// 获取传感器数据
const fetchSensorData = async () => {
  try {
    // 使用新的API获取传感器数据
    const response = await getRealtimeSensorData()
    console.log('获取传感器数据响应:', response)
    
    // 处理响应数据
    const processedData = processSensorDataResponse(response)
    const sensorData = processedData.data
    
    // 更新数据源信息
    dataSource.value = processedData.source
    lastUpdate.value = new Date(processedData.timestamp || Date.now())
    connectionError.value = processedData.connectionError
    
    // 如果有连接错误但仍然有数据，显示警告
    if (processedData.connectionError && sensorData) {
      console.warn('设备连接错误，显示缓存数据:', processedData.connectionError)
      ElMessage.warning({
        message: `设备连接错误，显示${processedData.source === 'database' ? '数据库' : '默认'}数据`,
        duration: 3000,
        showClose: true
      })
    }
    
    // 如果没有数据，直接返回
    if (!sensorData) {
      console.error('未获取到传感器数据')
      return
    }
    
    // 更新指标数据
    updateMetrics(sensorData)
    
    // 更新图表数据
    updateChartData(sensorData)
    
    // 检查是否需要生成警报
    checkAlerts(sensorData)
    
  } catch (error) {
    console.error('获取传感器数据失败:', error)
    connectionError.value = error.message || '获取数据失败'
  }
}

// 更新指标数据
const updateMetrics = (sensorData) => {
  // 更新温度
  const tempMetric = metrics.value.find(m => m.id === 1)
  if (tempMetric && sensorData.air_temperature !== undefined) {
    tempMetric.value = Number(sensorData.air_temperature).toFixed(1)
    tempMetric.status = getStatusClass(sensorData.air_temperature, 15, 25, 30)
    tempMetric.statusText = getStatusText(tempMetric.status)
  }
  
  // 更新湿度
  const humidityMetric = metrics.value.find(m => m.id === 2)
  if (humidityMetric && sensorData.air_humidity !== undefined) {
    humidityMetric.value = Number(sensorData.air_humidity).toFixed(1)
    humidityMetric.status = getStatusClass(sensorData.air_humidity, 40, 60, 80)
    humidityMetric.statusText = getStatusText(humidityMetric.status)
  }
  
  // 更新土壤湿度
  const soilMetric = metrics.value.find(m => m.id === 3)
  if (soilMetric && sensorData.soil_moisture !== undefined) {
    soilMetric.value = Number(sensorData.soil_moisture).toFixed(1)
    soilMetric.status = getStatusClass(sensorData.soil_moisture, 30, 70, 90)
    soilMetric.statusText = getStatusText(soilMetric.status)
  }
  
  // 更新光照强度
  const lightMetric = metrics.value.find(m => m.id === 4)
  if (lightMetric && sensorData.light_intensity !== undefined) {
    lightMetric.value = Number(sensorData.light_intensity).toFixed(0)
    lightMetric.status = getStatusClass(sensorData.light_intensity, 200, 800, 2000)
    lightMetric.statusText = getStatusText(lightMetric.status)
  }
  
  // 更新CO2浓度
  const co2Metric = metrics.value.find(m => m.id === 5)
  if (co2Metric && sensorData.co2_concentration !== undefined) {
    co2Metric.value = Number(sensorData.co2_concentration).toFixed(0)
    co2Metric.status = getStatusClass(sensorData.co2_concentration, 300, 800, 1200)
    co2Metric.statusText = getStatusText(co2Metric.status)
  }
}

// 更新图表数据
const updateChartData = (sensorData) => {
  const now = new Date()
  const timeStr = now.toLocaleTimeString()
  
  // 限制数据点数量，保持最新的10个点
  const maxDataPoints = 10
  
  // 更新温度图表数据
  if (sensorData.air_temperature !== undefined) {
    temperatureData.value.push({
      time: timeStr,
      value: Number(sensorData.air_temperature)
    })
    if (temperatureData.value.length > maxDataPoints) {
      temperatureData.value.shift()
    }
  }
  
  // 更新湿度图表数据
  if (sensorData.air_humidity !== undefined) {
    humidityData.value.push({
      time: timeStr,
      value: Number(sensorData.air_humidity)
    })
    if (humidityData.value.length > maxDataPoints) {
      humidityData.value.shift()
    }
  }
  
  // 更新土壤湿度图表数据
  if (sensorData.soil_moisture !== undefined) {
    soilMoistureData.value.push({
      time: timeStr,
      value: Number(sensorData.soil_moisture)
    })
    if (soilMoistureData.value.length > maxDataPoints) {
      soilMoistureData.value.shift()
    }
  }
  
  // 更新光照强度图表数据
  if (sensorData.light_intensity !== undefined) {
    lightIntensityData.value.push({
      time: timeStr,
      value: Number(sensorData.light_intensity)
    })
    if (lightIntensityData.value.length > maxDataPoints) {
      lightIntensityData.value.shift()
    }
  }
}

// 检查是否需要生成警报
const checkAlerts = (sensorData) => {
  const now = new Date()
  
  // 检查温度
  if (sensorData.air_temperature > 30) {
    addAlert('温度过高，请注意降温', 'alert', now)
  } else if (sensorData.air_temperature < 15) {
    addAlert('温度过低，请注意保温', 'warning', now)
  }
  
  // 检查湿度
  if (sensorData.air_humidity > 80) {
    addAlert('空气湿度过高，请注意通风', 'warning', now)
  } else if (sensorData.air_humidity < 40) {
    addAlert('空气湿度过低，请注意加湿', 'warning', now)
  }
  
  // 检查土壤湿度
  if (sensorData.soil_moisture > 90) {
    addAlert('土壤过湿，请减少灌溉', 'alert', now)
  } else if (sensorData.soil_moisture < 30) {
    addAlert('土壤干燥，需要灌溉', 'warning', now)
  }
}

// 添加警报
const addAlert = (message, severity, timestamp) => {
  // 检查是否已存在相同的警报
  const existingAlert = alerts.value.find(a => a.message === message)
  if (existingAlert) {
    // 更新现有警报的时间戳
    existingAlert.timestamp = timestamp
    return
  }
  
  // 添加新警报
  alerts.value.push({
    id: Date.now(),
    message,
    severity,
    timestamp,
    status: 'triggered'
  })
  
  // 限制警报数量
  if (alerts.value.length > 10) {
    alerts.value.shift()
  }
}

// 获取状态类名
const getStatusClass = (value, lowThreshold, normalThreshold, highThreshold) => {
  if (value < lowThreshold || value > highThreshold) {
    return 'alert'
  } else if (value < normalThreshold || value > normalThreshold) {
    return 'warning'
  }
  return 'normal'
}

// 获取状态文本
const getStatusText = (status) => {
  switch (status) {
    case 'alert':
      return '异常'
    case 'warning':
      return '注意'
    default:
      return '正常'
  }
}

// 获取警报数据
const fetchAlerts = async () => {
  // 这里可以从API获取警报数据
  // 暂时不实现
}

onMounted(async () => {
  // 初始化数据
  await fetchSensorData()
  await fetchAlerts()
  
  // 设置定时更新（每10秒）
  setInterval(fetchSensorData, 10000)
  setInterval(fetchAlerts, 10000)
})
</script>

<style scoped>
.environment-dashboard {
  padding: 20px;
}

.data-source-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.data-source {
  font-weight: bold;
  padding: 5px 10px;
  border-radius: 15px;
}

.data-source.realtime {
  background: #e8f5e9;
  color: #2e7d32;
}

.data-source.cached {
  background: #fff3e0;
  color: #f57c00;
}

.last-update {
  color: #666;
}

.connection-error {
  color: #c62828;
  display: flex;
  align-items: center;
  gap: 5px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.data-card {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.value {
  font-size: 2em;
  font-weight: bold;
  margin: 10px 0;
}

.status {
  padding: 5px 10px;
  border-radius: 15px;
  font-size: 0.9em;
}

.status.normal {
  background: #e8f5e9;
  color: #2e7d32;
}

.status.warning {
  background: #fff3e0;
  color: #f57c00;
}

.status.alert {
  background: #ffebee;
  color: #c62828;
}

.charts-container {
  margin-top: 30px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.alerts-panel {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-top: 30px;
}

.alert-list {
  max-height: 300px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.alert-time {
  min-width: 100px;
  color: #666;
}

.alert-message {
  flex: 1;
  margin: 0 20px;
}

button {
  padding: 5px 15px;
  border: none;
  border-radius: 5px;
  background: #42b983;
  color: white;
  cursor: pointer;
}

button:hover {
  background: #3aa876;
}
</style>