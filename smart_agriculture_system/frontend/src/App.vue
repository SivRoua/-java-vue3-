<template>
  <div id="app-container">
    <router-view v-slot="{ Component }">
      <transition name="fade-transform" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { getConnectionStatus } from '@/api/device'
import { useControlStore } from '@/store/control'
import { useUserStore } from '@/store/user'

const controlStore = useControlStore()
const userStore = useUserStore()

// 在应用启动时检查设备连接状态和用户状态
onMounted(async () => {
  // 首先显示页面，提高感知性能
  await nextTick()
  
  try {
    // 并行处理用户信息和设备状态检查
    const promises = []
    
    // 检查用户登录状态
    if (userStore.token && !userStore.userInfo.id) {
      promises.push(
        userStore.fetchUserInfo().catch(error => {
          console.error('Failed to fetch user info:', error)
        })
      )
    }
    
    // 检查设备连接状态
    promises.push(
      getConnectionStatus().then(response => {
        console.log('应用启动时设备连接状态:', response)
        
        // 更新全局状态
        controlStore.updateConnectionStatus({
          isConnected: response.status === 'connected',
          message: response.message || (response.status === 'connected' ? '设备已连接' : '设备未连接'),
          host: response.host,
          port: response.port,
          lastHeartbeat: response.last_heartbeat
        })
        
        // 如果设备已连接，显示通知
        if (response.status === 'connected') {
          ElMessage.success({
            message: '设备已连接',
            duration: 2000,
            showClose: true,
            customClass: 'message-with-animation'
          })
        }
      }).catch(error => {
        console.error('检查设备连接状态失败:', error)
        
        // 更新全局状态为未连接
        controlStore.updateConnectionStatus({
          isConnected: false,
          message: '连接状态检查失败',
          host: '',
          port: 0,
          lastHeartbeat: null
        })
      })
    )
    
    // 等待所有任务完成，但不阻塞UI渲染
    await Promise.allSettled(promises)
  } catch (error) {
    console.error('应用初始化错误:', error)
  }
})
</script>

<style lang="scss">
html, body {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f7fa;
  background-image: linear-gradient(to bottom, #f8f9fa, #e9ecef);
  text-rendering: optimizeLegibility;
}

#app, #app-container {
  height: 100%;
  width: 100%;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

// Element Plus 样式覆盖
.el-menu {
  border-right: none !important;
}

.el-menu--collapse {
  width: 64px;
}

.el-menu-item {
  &.is-active {
    background-color: #263445 !important;
  }
}

// 图标样式
.el-icon {
  vertical-align: middle;
  margin-right: 5px;
  width: 24px;
  height: 24px;
  filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.1));
}

// 消息样式增强
.message-with-animation {
  animation: message-slide-in 0.3s ease-out;
}

@keyframes message-slide-in {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

// 路由过渡效果
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

// 增强文字渲染
.el-menu-item, .el-submenu__title {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  letter-spacing: 0.3px;
}

// 图表容器增强
.chart-wrapper {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transform: translateZ(0);
  backface-visibility: hidden;
}
</style> 