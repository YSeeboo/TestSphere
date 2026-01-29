/**
 * 测试执行相关 API
 */

import request from '@/utils/request'

/**
 * 执行记录列表项
 */
export interface ExecutionList {
  id: number
  status: string
  trigger_type: string
  created_at: string
}

/**
 * 执行详情
 */
export interface ExecutionDetail extends ExecutionList {
  logs: string | null
}

/**
 * 执行配置
 */
export interface ExecutionConfig {
  env?: string
  marker_expression?: string
  keyword_expression?: string
}

/**
 * 触发执行返回
 */
export interface RunTestResponse {
  id?: number
  execution_id?: number
  task_id?: string
  status?: string
  message?: string
}

/**
 * 获取项目执行记录列表
 */
export function getProjectExecutions(projectId: number): Promise<ExecutionList[]> {
  return request.get<ExecutionList[]>(`/projects/${projectId}/executions`)
}

/**
 * 获取执行详情
 */
export function getExecutionDetail(executionId: number): Promise<ExecutionDetail> {
  return request.get<ExecutionDetail>(`/test-executions/${executionId}`)
}

/**
 * 触发测试执行
 */
export function runTest(projectId: number, config: ExecutionConfig): Promise<RunTestResponse> {
  return request.post<RunTestResponse>(`/projects/${projectId}/run`, config)
}
