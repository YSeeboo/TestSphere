/**
 * Axios 请求封装
 * 统一处理请求/响应拦截、错误处理等
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json;charset=utf-8',
  },
})

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 在发送请求前做些什么
    // 从 Pinia Store 获取 Token 并添加到请求头
    // 注意：在拦截器内部导入以避免循环依赖
    try {
      const { useUserStore } = require('@/stores/user')
      const userStore = useUserStore()
      
      if (userStore.token && config.headers) {
        config.headers.Authorization = `Bearer ${userStore.token}`
      }
    } catch (error) {
      // 如果 store 尚未初始化，回退到 localStorage
      const token = localStorage.getItem('token')
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    
    return config
  },
  (error: AxiosError) => {
    // 请求错误处理
    console.error('Request Error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    // 对响应数据做些什么
    const res = response.data

    // 如果返回的状态码不在 2xx 范围内，则认为是错误
    if (response.status < 200 || response.status >= 300) {
      ElMessage.error(res.message || 'Request Error')
      return Promise.reject(new Error(res.message || 'Error'))
    }

    return res
  },
  (error: AxiosError) => {
    // 响应错误处理
    console.error('Response Error:', error)

    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 400:
          ElMessage.error((data as any)?.detail || '请求参数错误')
          break
        case 401:
          // 未授权错误：清除 token 并跳转到登录页
          ElMessage.error('登录已过期，请重新登录')
          
          // 调用 userStore.logout() 处理登出逻辑
          // 在拦截器内部导入以避免循环依赖
          try {
            const { useUserStore } = require('@/stores/user')
            const userStore = useUserStore()
            
            // 清除 token 和用户信息
            userStore.reset()
            
            // 强制刷新页面或跳转到登录页
            // 这里使用 window.location.href 防止路由守卫的影响
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
          } catch (e) {
            // 如果 store 尚未初始化，手动清除 localStorage 并跳转
            localStorage.removeItem('token')
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
          }
          break
        case 403:
          ElMessage.error('拒绝访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        case 503:
          ElMessage.error('服务暂时不可用')
          break
        default:
          ElMessage.error((data as any)?.detail || `请求失败 (${status})`)
      }
    } else if (error.request) {
      // 请求已发出，但没有收到响应
      ElMessage.error('网络错误，请检查您的网络连接')
    } else {
      // 在设置请求时触发了错误
      ElMessage.error(error.message || '请求失败')
    }

    return Promise.reject(error)
  }
)

// 导出 axios 实例
export default service

/**
 * 通用请求方法封装
 */
export const request = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, config)
  },

  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config)
  },

  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.put(url, data, config)
  },

  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.delete(url, config)
  },

  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.patch(url, data, config)
  },
}
