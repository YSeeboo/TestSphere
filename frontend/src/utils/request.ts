/**
 * Axios 请求封装
 * 统一处理请求/响应拦截、错误处理等
 */

import axios, {
  AxiosInstance,
  InternalAxiosRequestConfig,
  AxiosResponse,
  AxiosError,
  AxiosRequestConfig
} from 'axios'
import { ElMessage } from 'element-plus'

/**
 * API 错误响应类型
 */
export interface ApiErrorResponse {
  detail?: string
  message?: string
  errors?: Record<string, string[]>
}

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
    // 直接从 localStorage 读取 token，避免循环依赖
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error: AxiosError) => {
    // 请求错误处理
    console.error('Request Error:', error)
    return Promise.reject(error)
  }
)

// 防止多次显示 401 错误提示
let isHandling401 = false

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
  (error: AxiosError<ApiErrorResponse>) => {
    // 响应错误处理
    console.error('Response Error:', error)

    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 400:
          ElMessage.error(data?.detail || '请求参数错误')
          break
        case 401:
          // 避免在登录页面重复跳转和多次提示
          if (window.location.pathname === '/login') {
            break
          }

          // 防止多次处理 401 错误
          if (!isHandling401) {
            isHandling401 = true
            ElMessage.error('登录已过期，请重新登录')

            // 清除 token
            localStorage.removeItem('token')
            localStorage.removeItem('userInfo')

            // 使用 router 跳转（如果可用），否则使用 window.location
            setTimeout(() => {
              import('@/router').then(({ default: router }) => {
                router.push('/login')
                isHandling401 = false
              }).catch(() => {
                window.location.href = '/login'
                isHandling401 = false
              })
            }, 500)
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
          ElMessage.error(data?.detail || `请求失败 (${status})`)
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
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, config)
  },

  post<T = unknown, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config)
  },

  put<T = unknown, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    return service.put(url, data, config)
  },

  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.delete(url, config)
  },

  patch<T = unknown, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    return service.patch(url, data, config)
  },
}
