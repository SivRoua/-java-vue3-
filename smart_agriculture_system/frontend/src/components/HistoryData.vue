<template>
  <div class="history-data">
    <div class="filters">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateChange"
          />
        </el-form-item>
        <el-form-item label="设备">
          <el-select v-model="selectedDevice" placeholder="选择设备" @change="handleDeviceChange">
            <el-option
              v-for="device in devices"
              :key="device.id"
              :label="device.name"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 统计数据卡片 -->
    <div class="statistics-cards" v-if="historyData.length > 0">
      <el-row :gutter="20">
        <el-col :span="8" v-for="(stat, key) in statistics" :key="key">
          <el-card class="stat-card">
            <template #header>
              <div class="card-header">
                <span>{{ getStatTitle(key) }}</span>
              </div>
            </template>
            <div class="stat-content">
              <div class="stat-item">
                <span>平均值：</span>
                <span>{{ stat.avg }}{{ getUnit(key) }}</span>
              </div>
              <div class="stat-item">
                <span>最小值：</span>
                <span>{{ stat.min }}{{ getUnit(key) }}</span>
              </div>
              <div class="stat-item">
                <span>最大值：</span>
                <span>{{ stat.max }}{{ getUnit(key) }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 历史数据图表 -->
    <div class="charts" v-if="historyData.length > 0">
      <el-tabs v-model="activeChart">
        <el-tab-pane label="温度趋势" name="temperature">
          <div class="chart-container">
            <v-chart class="chart" :option="getChartOption('temperature')" :autoresize="true" />
          </div>
        </el-tab-pane>
        <el-tab-pane label="湿度趋势" name="humidity">
          <div class="chart-container">
            <v-chart class="chart" :option="getChartOption('humidity')" :autoresize="true" />
          </div>
        </el-tab-pane>
        <el-tab-pane label="土壤湿度趋势" name="soil_moisture">
          <div class="chart-container">
            <v-chart class="chart" :option="getChartOption('soil_moisture')" :autoresize="true" />
          </div>
        </el-tab-pane>
        <el-tab-pane label="光照强度趋势" name="light_intensity">
          <div class="chart-container">
            <v-chart class="chart" :option="getChartOption('light_intensity')" :autoresize="true" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 数据表格 -->
    <div class="data-table" v-if="historyData.length > 0">
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column label="温度(°C)" width="120">
          <template #default="scope">
            {{ scope.row.air_temperature || scope.row.temperature || 'N/A' }}
          </template>
        </el-table-column>
        <el-table-column label="湿度(%)" width="120">
          <template #default="scope">
            {{ scope.row.air_humidity || scope.row.humidity || 'N/A' }}
          </template>
        </el-table-column>
        <el-table-column label="土壤湿度(%)" width="120">
          <template #default="scope">
            {{ scope.row.soil_moisture || 'N/A' }}
          </template>
        </el-table-column>
        <el-table-column label="光照强度(lux)" width="120">
          <template #default="scope">
            {{ scope.row.light_intensity || 'N/A' }}
          </template>
        </el-table-column>
        <el-table-column label="CO2浓度(ppm)" width="120">
          <template #default="scope">
            {{ scope.row.co2_concentration || scope.row.co2_level || 'N/A' }}
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
    
    <!-- 没有数据时显示提示 -->
    <el-empty v-if="!historyData.length && !loading" description="暂无历史数据" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { historyApi } from '@/api/history'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import { ensureArray, safeParseFloat, safeParseInt, safeArrayOperation } from '@/utils/dataHelper'

// 状态变量
const dateRange = ref([])
const selectedDevice = ref('')
const devices = ref([])
const statistics = ref({})
const historyData = ref([])
const activeChart = ref('temperature')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 计算属性
const tableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return historyData.value.slice(start, end)
})

// 方法
const handleDateChange = () => {
  fetchData()
}

const handleDeviceChange = () => {
  fetchData()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  fetchData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchData()
}

const formatDate = (date) => {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const getStatTitle = (key) => {
  const titles = {
    temperature: '温度',
    air_temperature: '温度',
    humidity: '湿度',
    air_humidity: '湿度',
    soil_moisture: '土壤湿度',
    light_intensity: '光照强度',
    co2_level: 'CO2浓度',
    co2_concentration: 'CO2浓度',
    ph_value: 'pH值'
  }
  return titles[key] || key
}

const getUnit = (key) => {
  const units = {
    temperature: '°C',
    air_temperature: '°C',
    humidity: '%',
    air_humidity: '%',
    soil_moisture: '%',
    light_intensity: 'lux',
    co2_level: 'ppm',
    co2_concentration: 'ppm',
    ph_value: ''
  }
  return units[key] || ''
}

// 检测是否有温度数据并获取正确的属性名
const getTemperatureKey = (item) => {
  if (item.air_temperature !== undefined && item.air_temperature !== null) return 'air_temperature';
  if (item.temperature !== undefined && item.temperature !== null) return 'temperature';
  return null;
}

// 检测是否有湿度数据并获取正确的属性名
const getHumidityKey = (item) => {
  if (item.air_humidity !== undefined && item.air_humidity !== null) return 'air_humidity';
  if (item.humidity !== undefined && item.humidity !== null) return 'humidity';
  return null;
}

// 检测是否有CO2数据并获取正确的属性名
const getCO2Key = (item) => {
  if (item.co2_concentration !== undefined && item.co2_concentration !== null) return 'co2_concentration';
  if (item.co2_level !== undefined && item.co2_level !== null) return 'co2_level';
  return null;
}

const getChartOption = (type) => {
  // 确保historyData.value是数组
  const safeData = ensureArray(historyData.value);
  
  // 如果没有数据，返回空配置
  if (safeData.length === 0) {
    return {
      title: { text: '暂无数据' },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value' },
      series: [{ type: 'line', data: [] }]
    };
  }
  
  // 根据类型获取正确的数据键
  let dataKey = type;
  if (type === 'temperature') {
    safeData.forEach(item => {
      const key = getTemperatureKey(item);
      if (key) dataKey = key;
    });
  } else if (type === 'humidity') {
    safeData.forEach(item => {
      const key = getHumidityKey(item);
      if (key) dataKey = key;
    });
  } else if (type === 'co2_level') {
    safeData.forEach(item => {
      const key = getCO2Key(item);
      if (key) dataKey = key;
    });
  }
  
  // 安全地筛选和映射数据
  const data = safeArrayOperation(safeData, 'filter', item => {
    if (!item) return false;
    if (type === 'temperature') {
      return item.air_temperature !== undefined || item.temperature !== undefined;
    } else if (type === 'humidity') {
      return item.air_humidity !== undefined || item.humidity !== undefined;
    } else if (type === 'co2_level') {
      return item.co2_concentration !== undefined || item.co2_level !== undefined;
    } else {
      return item[type] !== undefined && item[type] !== null;
    }
  }).map(item => {
    let value;
    if (type === 'temperature') {
      value = safeParseFloat(item.air_temperature !== undefined ? item.air_temperature : item.temperature);
    } else if (type === 'humidity') {
      value = safeParseFloat(item.air_humidity !== undefined ? item.air_humidity : item.humidity);
    } else if (type === 'co2_level') {
      value = safeParseInt(item.co2_concentration !== undefined ? item.co2_concentration : item.co2_level);
    } else {
      value = safeParseFloat(item[type]);
    }
    
    return {
      value: value,
      time: formatDate(item.timestamp)
    };
  });

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const [param] = params
        return `${param.data.time}<br/>${getStatTitle(type)}: ${param.data.value}${getUnit(type)}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.time),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: getStatTitle(type) + getUnit(type)
    },
    series: [{
      name: getStatTitle(type),
      type: 'line',
      smooth: true,
      data: data.map(item => item.value),
      markPoint: {
        data: [
          { type: 'max', name: '最大值' },
          { type: 'min', name: '最小值' }
        ]
      }
    }],
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100
      }
    ]
  }
}

const fetchData = async () => {
  try {
    // 获取历史数据
    const params = {};

    // 处理日期范围
    if (dateRange.value && dateRange.value.length === 2) {
      const [startDate, endDate] = dateRange.value;
      if (startDate && endDate) {
        params.start_date = startDate;
        params.end_date = endDate;
        console.log('使用日期范围查询:', params);
      }
    } else {
      // 如果没有选择日期范围，使用默认的24小时范围
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24);
      params.start_date = dayjs(start).format('YYYY-MM-DD');
      params.end_date = dayjs(end).format('YYYY-MM-DD');
      console.log('使用默认时间范围:', params);
    }

    // 添加设备ID
    if (selectedDevice.value) {
      params.device_id = selectedDevice.value;
    }
    
    const historyResponse = await historyApi.getHistoryData(params);
    
    console.log('历史数据响应:', historyResponse);
    
    // 使用我们的辅助方法确保数据是数组
    historyData.value = ensureArray(historyResponse);
    
    console.log(`处理后的数据: ${historyData.value.length} 条记录`);
    
    if (historyData.value.length === 0) {
      ElMessage.warning('未找到符合条件的历史数据');
    } else {
      ElMessage.success(`成功获取 ${historyData.value.length} 条历史数据`);
    }
    
    total.value = historyData.value.length;

    // 计算简单统计数据
    calculateStatistics();
    
  } catch (error) {
    console.error('Error fetching data:', error)
    ElMessage.error('获取数据失败: ' + (error.message || '未知错误'))
    historyData.value = [];
    statistics.value = {};
  }
}

// 手动计算统计数据
const calculateStatistics = () => {
  if (!Array.isArray(historyData.value) || historyData.value.length === 0) {
    statistics.value = {};
    return;
  }
  
  // 首先检查数据中使用的字段名称
  const firstItem = historyData.value[0] || {};
  const temperatureKey = getTemperatureKey(firstItem) || 'temperature';
  const humidityKey = getHumidityKey(firstItem) || 'humidity';
  const co2Key = getCO2Key(firstItem) || 'co2_level';
  
  const stats = {};
  const dataTypes = [
    { key: temperatureKey, name: 'temperature' },
    { key: humidityKey, name: 'humidity' },
    { key: 'soil_moisture', name: 'soil_moisture' },
    { key: 'light_intensity', name: 'light_intensity' },
    { key: co2Key, name: 'co2_level' }
  ];
  
  dataTypes.forEach(({ key, name }) => {
    if (!key) return;
    
    // 使用安全的数组操作方法
    const values = safeArrayOperation(
      historyData.value, 
      'filter', 
      item => item && item[key] !== undefined && item[key] !== null
    ).map(item => safeParseFloat(item[key]));
    
    if (values.length > 0) {
      // 使用安全的reduce操作
      const sum = safeArrayOperation(values, 'reduce', (acc, val) => acc + val, 0);
      stats[name] = {
        avg: (sum / values.length).toFixed(2),
        min: Math.min(...values).toFixed(2),
        max: Math.max(...values).toFixed(2)
      };
    } else {
      stats[name] = { avg: 'N/A', min: 'N/A', max: 'N/A' };
    }
  });
  
  statistics.value = stats;
}

// 生命周期钩子
onMounted(() => {
  // 设置默认时间范围为最近24小时
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - 3600 * 1000 * 24)
  dateRange.value = [dayjs(start).format('YYYY-MM-DD'), dayjs(end).format('YYYY-MM-DD')]
  
  // 获取数据
  fetchData()
})
</script>

<style lang="scss" scoped>
.history-data {
  padding: 20px;

  .filters {
    margin-bottom: 20px;
  }

  .statistics-cards {
    margin-bottom: 20px;

    .stat-card {
      .card-header {
        font-weight: bold;
      }

      .stat-content {
        .stat-item {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;

          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }
  }

  .charts {
    margin-bottom: 20px;

    .chart-container {
      height: 400px;
      width: 100%;

      .chart {
        height: 100%;
        width: 100%;
      }
    }
  }

  .data-table {
    .pagination {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style> 
