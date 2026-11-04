<template>
  <div class="api-debug">
    <h2>API调试页面</h2>
    
    <el-card class="debug-card">
      <template #header>
        <div class="card-header">
          <span>API测试工具</span>
        </div>
      </template>
      
      <el-form :inline="true">
        <el-form-item label="API路径">
          <el-select v-model="selectedApi" placeholder="选择API">
            <el-option
              v-for="api in apiList"
              :key="api.path"
              :label="api.name"
              :value="api.path"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="fetchData" :loading="loading">测试</el-button>
        </el-form-item>
      </el-form>
      
      <el-collapse v-if="response">
        <el-collapse-item title="原始响应数据" name="raw">
          <pre class="response-data">{{ JSON.stringify(response, null, 2) }}</pre>
        </el-collapse-item>
        
        <el-collapse-item title="数据类型分析" name="types">
          <div class="data-types">
            <p>响应类型: {{ typeof response }}</p>
            <p>是否数组: {{ Array.isArray(response) }}</p>
            <p v-if="Array.isArray(response)">数组长度: {{ response.length }}</p>
            <p v-if="Array.isArray(response) && response.length > 0">
              第一项类型: {{ typeof response[0] }}
            </p>
            <p v-if="Array.isArray(response) && response.length > 0">
              第一项数据:
            </p>
            <pre v-if="Array.isArray(response) && response.length > 0">{{ JSON.stringify(response[0], null, 2) }}</pre>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="数据验证" name="validation">
          <div class="validation">
            <h4>检查includes方法</h4>
            <div v-if="Array.isArray(response)">
              <p>测试: response.includes 是 {{ typeof response.includes === 'function' ? '函数' : '不是函数' }}</p>
              <el-button 
                @click="testIncludes" 
                :disabled="typeof response.includes !== 'function'"
                size="small"
              >
                测试includes
              </el-button>
              <p v-if="includesResult !== null">结果: {{ includesResult }}</p>
            </div>
            <div v-else>
              <p>不是数组，无法测试includes</p>
            </div>
            
            <h4>检查reduce方法</h4>
            <div v-if="Array.isArray(response)">
              <p>测试: response.reduce 是 {{ typeof response.reduce === 'function' ? '函数' : '不是函数' }}</p>
              <el-button 
                @click="testReduce" 
                :disabled="typeof response.reduce !== 'function'"
                size="small"
              >
                测试reduce
              </el-button>
              <p v-if="reduceResult !== null">结果: {{ reduceResult }}</p>
            </div>
            <div v-else>
              <p>不是数组，无法测试reduce</p>
            </div>
            
            <h4>数据结构检查</h4>
            <div v-if="Array.isArray(response) && response.length > 0">
              <p>检查第一项是否包含所需字段:</p>
              <ul>
                <li v-for="field in requiredFields" :key="field">
                  {{ field }}: {{ response[0][field] !== undefined ? '存在' : '不存在' }}
                </li>
              </ul>
            </div>
            <div v-else>
              <p>没有数据项可供检查</p>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
      
      <div v-if="error" class="error-message">
        <h4>错误信息</h4>
        <p>{{ error }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const selectedApi = ref('/api/history/data');
const response = ref(null);
const loading = ref(false);
const error = ref(null);
const includesResult = ref(null);
const reduceResult = ref(null);

const apiList = [
  { name: '历史数据', path: '/api/history/data' },
  { name: '历史数据(兼容)', path: '/api/history' },
  { name: '传感器数据', path: '/api/sensor/data' },
  { name: '设备状态', path: '/api/device/status' },
];

const requiredFields = [
  'timestamp',
  'air_temperature',
  'air_humidity',
  'soil_temperature',
  'soil_moisture',
  'light_intensity',
  'co2_concentration',
];

const fetchData = async () => {
  loading.value = true;
  error.value = null;
  response.value = null;
  includesResult.value = null;
  reduceResult.value = null;
  
  try {
    const resp = await axios.get(`http://localhost:5000${selectedApi.value}`);
    console.log('API响应:', resp);
    
    response.value = resp.data;
    
    // 安全地检查数据类型
    console.log('响应类型:', typeof response.value);
    console.log('是否数组:', Array.isArray(response.value));
    
    if (Array.isArray(response.value) && response.value.length > 0) {
      console.log('第一项类型:', typeof response.value[0]);
      console.log('第一项数据:', response.value[0]);
    }
    
    ElMessage.success('API请求成功');
  } catch (err) {
    console.error('API请求失败:', err);
    error.value = err.message || '请求失败';
    ElMessage.error(`API请求失败: ${error.value}`);
  } finally {
    loading.value = false;
  }
};

const testIncludes = () => {
  try {
    if (Array.isArray(response.value)) {
      // 测试includes方法
      const testValue = response.value[0];
      const result = response.value.includes(testValue);
      includesResult.value = `includes测试成功: ${result}`;
    } else {
      includesResult.value = '不是数组，无法测试includes';
    }
  } catch (err) {
    console.error('测试includes失败:', err);
    includesResult.value = `测试失败: ${err.message}`;
  }
};

const testReduce = () => {
  try {
    if (Array.isArray(response.value)) {
      // 测试reduce方法
      const result = response.value.reduce((sum, item) => {
        return sum + 1;
      }, 0);
      reduceResult.value = `reduce测试成功: 总计 ${result} 项`;
    } else {
      reduceResult.value = '不是数组，无法测试reduce';
    }
  } catch (err) {
    console.error('测试reduce失败:', err);
    reduceResult.value = `测试失败: ${err.message}`;
  }
};

onMounted(() => {
  // 页面加载时自动执行一次请求
  fetchData();
});
</script>

<style scoped>
.api-debug {
  padding: 20px;
}

.debug-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.response-data {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  overflow: auto;
  max-height: 300px;
  font-family: monospace;
  white-space: pre-wrap;
}

.data-types, .validation {
  margin-top: 10px;
}

.error-message {
  margin-top: 20px;
  color: #f56c6c;
  background-color: #fef0f0;
  padding: 10px;
  border-radius: 4px;
}
</style> 