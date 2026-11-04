import { defineStore } from 'pinia'
import { login as loginApi, getUserInfo, refreshToken, logout as logoutApi, register as registerApi } from '@/api/user'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { safeJSONParse, getAvatarUrl } from '@/utils/common'

export const useUserStore = defineStore('user', {
  state: () => {
    // 安全地从localStorage读取数据
    const token = localStorage.getItem('access_token') || '';
    const userInfoStr = localStorage.getItem('userInfo');
    const userInfo = safeJSONParse(userInfoStr, {});
    
    return {
      token,
      userInfo,
      roles: userInfo.role ? [userInfo.role] : [],
      permissions: []
    };
  },

  getters: {
    isLoggedIn: (state) => !!state.token,
    username: (state) => state.userInfo?.username || '',
    userRole: (state) => state.userInfo?.role || '',
    avatar: (state) => getAvatarUrl(state.userInfo?.avatar || 'avator.png')
  },

  actions: {
    // 登录
    async login(userInfo) {
      try {
        const { username, password } = userInfo
        console.log('正在尝试登录:', username)
        
        const response = await loginApi({ username: username.trim(), password })
        console.log('登录响应:', response)
        
        // 处理不同的响应格式
        let access_token, user
        
        if (response.data) {
          // 如果响应被axios包装在data字段
          access_token = response.data.access_token
          user = response.data.user
        } else {
          // 直接响应
          access_token = response.access_token
          user = response.user
        }
        
        if (!access_token || !user) {
          console.error('Invalid login response format:', response)
          ElMessage.error('服务器返回数据格式错误')
          return false
        }

        // 保存token到localStorage和state
        localStorage.setItem('access_token', access_token)
        this.token = access_token

        // 设置默认头像
        if (!user.avatar) {
          user.avatar = 'avator.png'
        }

        // 保存用户信息
        localStorage.setItem('userInfo', JSON.stringify(user))
        this.userInfo = user
        this.roles = user.role ? [user.role] : []

        return true
      } catch (error) {
        console.error('Login failed:', error)
        const errorMessage = error.response?.data?.error || 
                            (error.message || '登录失败')
        ElMessage.error(errorMessage)
        return false
      }
    },

    // 注册
    async register(registerInfo) {
      try {
        const response = await registerApi(registerInfo)
        ElMessage.success('注册成功，请登录')
        return true
      } catch (error) {
        console.error('Registration failed:', error)
        const errorMessage = error.response?.data?.error || 
                           (error.message || '注册失败')
        ElMessage.error(errorMessage)
        return false
      }
    },

    // 获取用户信息
    async fetchUserInfo() {
      try {
        const response = await getUserInfo()
        console.log('获取用户信息响应:', response)
        
        // 确保响应中包含用户数据
        if (!response) {
          console.error('Empty response when fetching user info')
          return null
        }
        
        // 处理不同的响应格式
        const userInfo = response.data || response
        
        if (!userInfo || typeof userInfo !== 'object') {
          console.error('Invalid user info format:', userInfo)
          return null
        }
        
        // 设置默认头像
        if (!userInfo.avatar) {
          userInfo.avatar = 'avator.png'
        }
        
        // 保存用户信息到localStorage和state
        localStorage.setItem('userInfo', JSON.stringify(userInfo))
        this.userInfo = userInfo
        
        // 确保role字段存在
        if (userInfo.role) {
          this.roles = [userInfo.role]
        } else {
          this.roles = []
        }

        return userInfo
      } catch (error) {
        console.error('Failed to fetch user info:', error)
        return null
      }
    },

    // 登出 - 改为不依赖API的同步方法
    logout() {
      try {
        // 不再调用API，直接清除本地状态
        // 可选：在后台尝试调用登出API，但不等待结果
        this.callLogoutApi()
        
        // 清除所有状态和本地存储
        localStorage.removeItem('access_token')
        localStorage.removeItem('userInfo')
        this.token = ''
        this.userInfo = {}
        this.roles = []
        this.permissions = []
        
        // 重定向到登录页
        router.push('/login')
        
        ElMessage.success('退出登录成功')
        return true
      } catch (error) {
        console.error('Logout error:', error)
        // 即使有错误也要清除状态并跳转
        localStorage.removeItem('access_token')
        localStorage.removeItem('userInfo')
        this.token = ''
        this.userInfo = {}
        this.roles = []
        this.permissions = []
        
        router.push('/login')
        return true
      }
    },
    
    // 在后台调用登出API，但不阻塞主流程
    async callLogoutApi() {
      try {
        await logoutApi()
        console.log('登出API调用成功')
      } catch (error) {
        console.warn('登出API调用失败，但不影响本地登出流程:', error)
      }
    },

    // 刷新token
    async refreshToken() {
      try {
        const response = await refreshToken()
        
        if (!response) {
          console.error('Empty refresh token response')
          return false
        }
        
        const data = response.data || response
        const access_token = data.access_token
        const user = data.user
        
        if (!access_token || !user) {
          console.error('Invalid refresh token response:', response)
          return false
        }

        // 设置默认头像
        if (!user.avatar) {
          user.avatar = 'avator.png'
        }

        localStorage.setItem('access_token', access_token)
        this.token = access_token
        
        // 更新用户信息
        localStorage.setItem('userInfo', JSON.stringify(user))
        this.userInfo = user
        this.roles = user.role ? [user.role] : []

        return true
      } catch (error) {
        console.error('Failed to refresh token:', error)
        this.logout()
        return false
      }
    }
  }
}) 