<template>
  <div class="chart-container">
    <h2>{{ title }}</h2>
    <div class="chart" ref="chartContainer"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: String,
  data: Array,
  type: String
})

const chartContainer = ref(null)
let chart = null

const initChart = () => {
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartContainer.value)
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'time',
      axisLabel: {
        formatter: (value) => {
          const date = new Date(value)
          return `${date.getHours()}:${date.getMinutes()}`
        }
      }
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      data: props.data,
      type: 'line',
      smooth: true
    }]
  }
  
  chart.setOption(option)
}

onMounted(() => {
  initChart()
})

watch(() => props.data, () => {
  initChart()
}, { deep: true })
</script>

<style scoped>
.chart-container {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin: 20px 0;
}

.chart {
  height: 300px;
  width: 100%;
}
</style>