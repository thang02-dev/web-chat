import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('access_token') || null)
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')

  async function login(usernameOrEmail, password) {
    loading.value = true
    error.value = null
    try {
      const res = await api.post('/auth/login', {
        username_or_email: usernameOrEmail,
        password: password
      })
      const data = res.data
      token.value = data.access_token
      user.value = data.user
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      return data.user
    } catch (err) {
      error.value = err.response?.data?.detail || 'Đăng nhập không thành công.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(userData) {
    loading.value = true
    error.value = null
    try {
      const res = await api.post('/auth/register', userData)
      // Automatically login after successful registration
      return await login(userData.username, userData.password)
    } catch (err) {
      error.value = err.response?.data?.detail || 'Đăng ký tài khoản thất bại.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return null
    try {
      const res = await api.get('/auth/me')
      user.value = res.data
      localStorage.setItem('user', JSON.stringify(res.data))
      return res.data
    } catch (err) {
      if (err.response?.status === 401) {
        logout()
      }
      return null
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    login,
    register,
    fetchCurrentUser,
    logout
  }
})

