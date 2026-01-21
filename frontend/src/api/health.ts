/**
 * 健康检查相关 API
 */

import { request } from '@/utils/request'

export interface HealthResponse {
  status: string
  service: string
  version: string
  database: string
  redis: string
}

/**
 * 健康检查
 */
export const getHealth = () => {
  return request.get<HealthResponse>('/health')
}

/**
 * 就绪检查
 */
export const getReadiness = () => {
  return request.get<{ status: string }>('/health/ready')
}

/**
 * 存活检查
 */
export const getLiveness = () => {
  return request.get<{ status: string }>('/health/live')
}
