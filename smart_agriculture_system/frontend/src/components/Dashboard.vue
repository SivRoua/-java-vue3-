<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 数据概览卡片 -->
      <el-col :span="6">
        <el-card class="data-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Sunny /></el-icon>
              <span>平均温度</span>
            </div>
          </template>
          <div class="card-value">
            {{ sensorData.temperature }}°C
            <span class="trend" :class="{ up: tempTrend > 0, down: tempTrend < 0 }">
              {{ tempTrend > 0 ? '+' : '' }}{{ tempTrend }}%
            </span>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="data-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Cloudy /></el-icon>
              <span>平均湿度</span>
            </div>
          </template>
          <div class="card-value">
            {{ sensorData.humidity }}%
            <span class="trend" :class="{ up: humidityTrend > 0, down: humidityTrend < 0 }">
              {{ humidityTrend > 0 ? '+' : '' }}{{ humidityTrend }}%
            </span>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="data-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Bell /></el-icon>
              <span>今日警报</span>
            </div>
          </template>
          <div class="card-value">
            {{ alertCount }}
            <span class="trend" :class="{ up: alertTrend > 0, down: alertTrend < 0 }">
              {{ alertTrend > 0 ? '+' : '' }}{{ alertTrend }}%
            </span>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="data-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Monitor /></el-icon>
              <span>设备在线</span>
            </div>
          </template>
          <div class="card-value">
            {{ onlineDevices }}/{{ totalDevices }}
            <span class="percentage">{{ ((onlineDevices/totalDevices) * 100).toFixed(1) }}%</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 24小时温湿度趋势图 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>24小时温湿度趋势</span>
              <el-radio-group v-model="chartTimeRange" size="small">
                <el-radio-button label="24h">24小时</el-radio-button>
                <el-radio-button label="7d">7天</el-radio-button>
                <el-radio-button label="30d">30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <v-chart class="chart" :option="chartOption" autoresize />
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="device-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>设备状态</span>
              <el-button type="primary" size="small" @click="refreshDevices">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="device-list">
            <div v-for="device in devices" :key="device.id" class="device-item">
              <div class="device-info">
                <el-tag :type="device.status === 'active' ? 'success' : 'danger'" size="small">
                  {{ device.status === 'active' ? '在线' : '离线' }}
                </el-tag>
                <span class="device-name">{{ device.name }}</span>
              </div>
              <div class="device-controls">
                <el-switch
                  v-model="device.isOn"
                  :loading="device.loading"
                  @change="(val) => handleDeviceControl(device, val)"
                />
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useMonitorStore } from '@/store/monitor'
import { getDeviceStatus, controlDevice } from '@/api/device'
import { ElMessage } from 'element-plus'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'

// 注册ECharts组件
use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const monitorStore = useMonitorStore()
const chartTimeRange = ref('24h')
const updateInterval = ref(null)
const devices = ref([])
const onlineDevices = ref(0)
const totalDevices = ref(0)
const alertCount = ref(0)
const tempTrend = ref(2.1)
const humidityTrend = ref(-1.5)
const alertTrend = ref(50)

// 图表配置
const chartOption = ref({
  tooltip: {
    trigger: 'axis',
    formatter: '{b}<br />{a0}: {c0}°C<br />{a1}: {c1}%'
  },
  legend: {
    data: ['温度', '湿度']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: []
  },
  yAxis: [
    {
      type: 'value',
      name: '温度(°C)',
      position: 'left'
    },
    {
      type: 'value',
      name: '湿度(%)',
      position: 'right'
    }
  ],
  series: [
    {
      name: '温度',
      type: 'line',
      smooth: true,
      data: [],
      itemStyle: {
        color: '#FF9F43'
      }
    },
    {
      name: '湿度',
      type: 'line',
      smooth: true,
      data: [],
      itemStyle: {
        color: '#00CFE8'
      }
    }
  ]
})

// 获取设备状态
const fetchDeviceStatus = async () => {
  try {
    const response = await getDeviceStatus()
    if (response.data) {
      devices.value = response.data.devices.map(device => ({
        ...device,
        isOn: device.status === 'active',
        loading: false
      }))
      onlineDevices.value = devices.value.filter(d => d.status === 'active').length
      totalDevices.value = devices.value.length
    }
  } catch (error) {
    console.error('获取设备状态失败:', error)
    ElMessage.error('获取设备状态失败')
  }
}

// 控制设备
const handleDeviceControl = async (device, value) => {
  device.loading = true
  try {
    await controlDevice(device.id, value ? 'on' : 'off')
    device.isOn = value
    ElMessage.success(`${device.name}${value ? '已开启' : '已关闭'}`)
  } catch (error) {
    device.isOn = !value // 恢复状态
    ElMessage.error(`操作失败: ${error.message}`)
  } finally {
    device.loading = false
  }
}

// 刷新设备列表
const refreshDevices = () => {
  fetchDeviceStatus()
}

// 更新图表数据
const updateChartData = () => {
  const now = new Date()
  const times = []
  const temps = []
  const humids = []
  
  // 生成24小时的时间点
  for (let i = 0; i < 24; i++) {
    const time = new Date(now - (23 - i) * 3600 * 1000)
    times.push(time.getHours().toString().padStart(2, '0') + ':00')
  }
  
  chartOption.value.xAxis.data = times
  chartOption.value.series[0].data = monitorStore.historyData.map(d => d.temperature)
  chartOption.value.series[1].data = monitorStore.historyData.map(d => d.humidity)
}

onMounted(async () => {
  // 获取初始数据
  await fetchDeviceStatus()
  await monitorStore.fetchHistoryData({ range: '24h' })
  updateChartData()
  
  // 设置定时更新（每120秒/2分钟）
  updateInterval.value = setInterval(() => {
    fetchDeviceStatus()
    monitorStore.fetchRealTimeData()
  }, 120000)
})

onUnmounted(() => {
  if (updateInterval.value) {
    clearInterval(updateInterval.value)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.data-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.trend {
  font-size: 14px;
  &.up { color: #FF4949; }
  &.down { color: #13CE66; }
}

.percentage {
  font-size: 14px;
  color: #8c8c8c;
}

.chart-row {
  margin-top: 20px;
}

.chart-card {
  height: 400px;
}

.chart {
  height: 100%;
}

.device-card {
  height: 400px;
  overflow-y: auto;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border-radius: 4px;
  background: #f5f7fa;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-name {
  font-weight: 500;
}

:deep(.el-card__header) {
  padding: 12px 20px;
  border-bottom: 1px solid #e4e7ed;
}
</style>