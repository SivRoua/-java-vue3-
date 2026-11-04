<template>
  <el-container class="layout-container">
    <el-aside width="200px" class="aside">
      <div class="logo">
        <img src="@/assets/logo.png" alt="Logo">
        <span>智能农业系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="menu"
        :collapse="isCollapse"
        @select="handleSelect"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <template #title>控制面板</template>
        </el-menu-item>
        <el-menu-item index="/monitor">
          <el-icon><DataLine /></el-icon>
          <template #title>环境监测</template>
        </el-menu-item>
        <el-menu-item index="/control">
          <el-icon><Setting /></el-icon>
          <template #title>设备控制</template>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <template #title>警报管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon 
            class="collapse-btn"
            @click="toggleCollapse"
          >
            <Fold v-if="!isCollapse"/>
            <Expand v-else/>
          </el-icon>
          <breadcrumb />
        </div>
        
        <div class="header-right">
          <el-badge :value="3" class="notice-badge">
            <el-icon><Bell /></el-icon>
          </el-badge>
          
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="avatar-container">
              <el-avatar 
                :size="32"
                :src="userStore.userInfo.avatar || defaultAvatar"
              />
              <span class="username">{{ userStore.username }}</span>
              <el-icon><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人信息
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import Breadcrumb from '@/components/Breadcrumb.vue'
import defaultAvatar from '@/assets/default-avatar.png'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleSelect = (key) => {
  router.push(key)
}

const handleCommand = async (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      await userStore.logout()
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.aside {
  background-color: #304156;
  transition: width 0.3s;
  overflow-x: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  
  img {
    width: 32px;
    height: 32px;
    margin-right: 8px;
  }
}

.menu {
  border: none;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  &:hover {
    color: #409EFF;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.notice-badge {
  cursor: pointer;
  font-size: 20px;
  
  :deep(.el-badge__content) {
    background-color: #ff4949;
  }
}

.avatar-container {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  
  &:hover {
    background: #f5f7fa;
  }
  
  .username {
    font-size: 14px;
    color: #606266;
  }
}

.main {
  background: #f0f2f5;
  padding: 16px;
}

/* 路由切换动画 */
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
</style> 