<template>
  <div class="control-panel">
    <!-- 遮阳系统 -->
    <section class="control-panel__section">
      <h2>遮阳系统控制</h2>
      <div class="control-panel__grid">
        <!-- 外遮阳 -->
        <div class="control-panel__card">
          <div class="control-panel__card-header">
            <img :src="deviceStatus.external_shade ? '/src/assets/images/外遮阳开.png' : '/src/assets/images/外遮阳关.png'" 
                 :alt="deviceStatus.external_shade ? '外遮阳开启' : '外遮阳关闭'">
            <h3>外遮阳</h3>
          </div>
          <div class="control-panel__card-content">
            <div class="control-panel__status" 
                 :class="deviceStatus.external_shade ? 'control-panel__status--on' : 'control-panel__status--off'">
              {{ deviceStatus.external_shade ? '开启' : '关闭' }}
            </div>
            <div class="control-panel__controls">
              <button class="btn btn-primary" 
                      @click="controlDevice('external_shade', 'on')"
                      :disabled="deviceStatus.external_shade">
                开启
              </button>
              <button class="btn btn-danger"
                      @click="controlDevice('external_shade', 'off')"
                      :disabled="!deviceStatus.external_shade">
                关闭
              </button>
            </div>
          </div>
        </div>

        <!-- 内遮阳 -->
        <div class="control-panel__card">
          <div class="control-panel__card-header">
            <img :src="deviceStatus.internal_shade ? '/src/assets/images/内遮阳开.png' : '/src/assets/images/内遮阳关.png'"
                 :alt="deviceStatus.internal_shade ? '内遮阳开启' : '内遮阳关闭'">
            <h3>内遮阳</h3>
          </div>
          <div class="control-panel__card-content">
            <div class="control-panel__status"
                 :class="deviceStatus.internal_shade ? 'control-panel__status--on' : 'control-panel__status--off'">
              {{ deviceStatus.internal_shade ? '开启' : '关闭' }}
            </div>
            <div class="control-panel__controls">
              <button class="btn btn-primary"
                      @click="controlDevice('internal_shade', 'on')"
                      :disabled="deviceStatus.internal_shade">
                开启
              </button>
              <button class="btn btn-danger"
                      @click="controlDevice('internal_shade', 'off')"
                      :disabled="!deviceStatus.internal_shade">
                关闭
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 通风系统 -->
    <section class="control-panel__section">
      <h2>通风系统控制</h2>
      <div class="control-panel__grid">
        <!-- 外通风 -->
        <div class="control-panel__card">
          <div class="control-panel__card-header">
            <img src="/src/assets/images/外通风.gif" alt="外通风">
            <h3>外通风</h3>
          </div>
          <div class="control-panel__card-content">
            <div class="control-panel__status"
                 :class="deviceStatus.external_ventilation ? 'control-panel__status--on' : 'control-panel__status--off'">
              {{ deviceStatus.external_ventilation ? '运行中' : '已停止' }}
            </div>
            <div class="control-panel__controls">
              <button class="btn btn-primary"
                      @click="controlDevice('external_ventilation', 'on')"
                      :disabled="deviceStatus.external_ventilation">
                启动
              </button>
              <button class="btn btn-danger"
                      @click="controlDevice('external_ventilation', 'off')"
                      :disabled="!deviceStatus.external_ventilation">
                停止
              </button>
            </div>
          </div>
        </div>

        <!-- 内通风 -->
        <div class="control-panel__card">
          <div class="control-panel__card-header">
            <img src="/src/assets/images/内通风.gif" alt="内通风">
            <h3>内通风</h3>
          </div>
          <div class="control-panel__card-content">
            <div class="control-panel__status"
                 :class="deviceStatus.internal_ventilation ? 'control-panel__status--on' : 'control-panel__status--off'">
              {{ deviceStatus.internal_ventilation ? '运行中' : '已停止' }}
            </div>
            <div class="control-panel__controls">
              <button class="btn btn-primary"
                      @click="controlDevice('internal_ventilation', 'on')"
                      :disabled="deviceStatus.internal_ventilation">
                启动
              </button>
              <button class="btn btn-danger"
                      @click="controlDevice('internal_ventilation', 'off')"
                      :disabled="!deviceStatus.internal_ventilation">
                停止
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 水系统 -->
    <section class="control-panel__section">
      <h2>水系统控制</h2>
      <div class="control-panel__grid">
        <!-- 喷灌 -->
        <div class="control-panel__card">
          <div class="control-panel__card-header">
            <img src="/src/assets/images/喷灌.gif" alt="喷灌">
            <h3>喷灌系统</h3>
          </div>
          <div class="control-panel__card-content">
            <div class="control-panel__status"
                 :class="deviceStatus.sprinkler ? 'control-panel__status--on' : 'control-panel__status--off'">
              {{ deviceStatus.sprinkler ? '喷灌中' : '已关闭' }}
            </div>
            <div class="control-panel__controls">
              <button class="btn btn-primary"
                      @click="controlDevice('sprinkler', 'on')"
                      :disabled="deviceStatus.sprinkler">
                开启
              </button>
              <button class="btn btn-danger"
                      @click="controlDevice('sprinkler', 'off')"
                      :disabled="!deviceStatus.sprinkler">
                关闭
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const deviceStatus = ref({
  external_shade: false,
  internal_shade: false,
  external_ventilation: false,
  internal_ventilation: false,
  sprinkler: false
})

const controlDevice = async (deviceId, action) => {
  try {
    const response = await axios.post('/api/control-device', {
      device_id: deviceId,
      action: action
    })
    
    if (response.data.status === 'success') {
      deviceStatus.value[deviceId] = action === 'on'
    }
  } catch (error) {
    console.error('控制设备失败:', error)
  }
}

const getDeviceStatus = async () => {
  try {
    const response = await axios.get('/api/device-status')
    deviceStatus.value = response.data
  } catch (error) {
    console.error('获取设备状态失败:', error)
  }
}

onMounted(() => {
  getDeviceStatus()
  setInterval(getDeviceStatus, 120000) // 每120秒（2分钟）更新一次
})
</script>

<style lang="scss" scoped>
@use '../styles/components/control-panel.scss' as *;
</style>