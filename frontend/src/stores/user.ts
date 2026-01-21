/**
 * 用户状态管理 Store
 * 使用 Pinia Setup Syntax
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { login as loginApi, getMe } from '@/api/auth'
import type { UserInfo, UserLoginForm } from '@/types/user'

const TOKEN_KEY = 'token'

/**
 * 用户 Store
 */
export const useUserStore = defineStore('user', () => {
  // State: Token (从 localStorage 初始化)
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  
  // State: 用户信息
  const userInfo = ref<UserInfo | null>(null)

  // Computed: 是否已登录
  const isLoggedIn = computed(() => !!token.value)

  // Computed: 是否是超级管理员
  const isSuperUser = computed(() => userInfo.value?.is_superuser ?? false)

  /**
   * 设置 Token
   * @param newToken Token 字符串
   */
  function setToken(newToken: string | null) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem(TOKEN_KEY, newToken)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  /**
   * 设置用户信息
   * @param info 用户信息对象
   */
  function setUserInfo(info: UserInfo | null) {
    userInfo.value = info
  }

  /**
   * 获取当前用户信息
   * @returns Promise<void>
   */
  async function fetchUserInfo(): Promise<void> {
    try {
      const data = await getMe()
      setUserInfo(data)
    } catch (error) {
      console.error('Failed to fetch user info:', error)
      // 如果获取用户信息失败，清除 token
      setToken(null)
      setUserInfo(null)
      throw error
    }
  }

  /**
   * 用户登录
   * @param loginForm 登录表单数据
   * @returns Promise<void>
   */
  async function login(loginForm: UserLoginForm): Promise<void> {
    try {
      // 调用登录 API
      const tokenResponse = await loginApi(loginForm)
      
      // 保存 Token
      setToken(tokenResponse.access_token)
      
      // 获取用户信息
      await fetchUserInfo()
      
      // 登录成功提示
      ElMessage.success('登录成功')
      
      // 跳转到首页 (使用 replace 防止返回到登录页)
      await router.replace('/')
    } catch (error: any) {
      console.error('Login failed:', error)
      
      // 登录失败，清除 token
      setToken(null)
      setUserInfo(null)
      
      // 错误提示
      const errorMessage = error.response?.data?.detail || error.message || '登录失败'
      ElMessage.error(errorMessage)
      
      throw error
    }
  }

  /**
   * 用户登出
   */
  async function logout(): Promise<void> {
    // 清除 Token
    setToken(null)
    
    // 清除用户信息
    setUserInfo(null)
    
    // 提示
    ElMessage.success('已退出登录')
    
    // 跳转到登录页
    await router.push('/login')
  }

  /**
   * 重置 Store 状态
   */
  function reset() {
    setToken(null)
    setUserInfo(null)
  }

  return {
    // State
    token,
    userInfo,
    
    // Computed
    isLoggedIn,
    isSuperUser,
    
    // Actions
    setToken,
    setUserInfo,
    fetchUserInfo,
    login,
    logout,
    reset,
  }
})
