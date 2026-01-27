/**
 * 测试用例相关 API
 */

import request from '@/utils/request'
import type { TestCaseListResponse, TestCaseQueryParams } from '@/types/testCase'

/**
 * 获取项目的测试用例列表
 * @param projectId 项目 ID
 * @param params 查询参数 (limit, offset)
 * @returns Promise<TestCaseListResponse>
 */
export function getTestCases(
  projectId: number,
  params: TestCaseQueryParams
): Promise<TestCaseListResponse> {
  return request.get(`/projects/${projectId}/test-cases`, { params })
}
