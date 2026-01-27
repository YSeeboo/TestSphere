/**
 * 测试用例相关类型定义
 */

/**
 * 测试用例接口
 */
export interface TestCase {
  id: number
  project_id: number
  file_path: string
  name: string
  description: string | null
  nodeid: string
  markers: Record<string, any> | null
  created_at: string
  updated_at: string
}

/**
 * 测试用例查询参数
 */
export interface TestCaseQueryParams {
  limit?: number
  offset?: number
}

/**
 * 测试用例列表响应
 */
export interface TestCaseListResponse {
  items: TestCase[]
  total: number
}
