import request from '@/utils/request'
import { API_ENDPOINTS } from '@/config/api'

export function login(data) {
  return request({
    url: API_ENDPOINTS.LOGIN,
    method: 'post',
    data
  }).catch(error => {
    console.error('Login API error:', error)
    throw error
  })
}

export function register(data) {
  return request({
    url: '/api/auth/register',
    method: 'post',
    data: {
      username: data.username,
      password: data.password,
      email: data.email,
      admin_username: data.admin_username,
      admin_password: data.admin_password
    }
  }).catch(error => {
    console.error('Register API error:', error)
    throw error
  })
}

export function getUserInfo() {
  return request({
    url: API_ENDPOINTS.USER_INFO,
    method: 'get'
  }).catch(error => {
    console.error('Get user info API error:', error)
    throw error
  })
}

export function logout() {
  return request({
    url: API_ENDPOINTS.LOGOUT,
    method: 'post'
  }).catch(error => {
    console.error('Logout API error:', error)
    // 即使API失败，我们仍然需要清理本地状态
    return { success: true, message: '已清除本地登录状态' }
  })
}

export function refreshToken() {
  return request({
    url: '/api/auth/refresh',
    method: 'post',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  }).catch(error => {
    console.error('Refresh token API error:', error)
    throw error
  })
}

export function changePassword(data) {
  return request({
    url: '/api/auth/change-password',
    method: 'post',
    data,
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  }).catch(error => {
    console.error('Change password API error:', error)
    throw error
  })
}

export function getUserList() {
  return request({
    url: API_ENDPOINTS.USER_LIST,
    method: 'get'
  })
}

export function createUser(data) {
  const token = localStorage.getItem('access_token')
  if (!token) {
    return Promise.reject(new Error('未登录或登录已过期'))
  }

  return request({
    url: API_ENDPOINTS.USER_CREATE,
    method: 'post',
    data: {
      username: data.username,
      email: data.email,
      password: data.password,
      role: data.role || 'user',
      is_active: data.status !== false
    },
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }).catch(error => {
    console.error('Create user API error:', error)
    if (error.response && error.response.data) {
      throw new Error(error.response.data.message || '创建用户失败')
    }
    throw error
  })
}

export function updateUser(id, data) {
  return request({
    url: `${API_ENDPOINTS.USER_UPDATE}/${id}`,
    method: 'put',
    data
  })
}

export function deleteUser(id) {
  return request({
    url: `${API_ENDPOINTS.USER_DELETE}/${id}`,
    method: 'delete'
  })
}