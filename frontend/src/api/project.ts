/**
 * 项目相关的 API 调用函数
 */

import request from '@/utils/request'
import type { Project, ProjectCreate, ProjectCreateForm, ProjectUpdateForm } from '@/types/project'

/**
 * 获取项目列表 API
 * @param skip 跳过记录数
 * @param limit 返回记录数上限
 * @returns 项目列表
 */
export function getProjects(skip: number = 0, limit: number = 100): Promise<Project[]> {
  return request.get<Project[]>('/projects/', {
    params: { skip, limit }
  })
}

/**
 * 创建项目 API
 * @param projectData 项目创建数据
 * @returns 创建的项目信息
 */
export function createProject(projectData: ProjectCreateForm): Promise<Project> {
  return request.post<Project>('/projects/', projectData)
}

/**
 * 获取单个项目 API
 * @param projectId 项目 ID
 * @returns 项目信息
 */
export function getProject(projectId: number): Promise<Project> {
  return request.get<Project>(`/projects/${projectId}`)
}

/**
 * 更新项目 API
 * @param projectId 项目 ID
 * @param projectData 项目更新数据
 * @returns 更新后的项目信息
 */
export function updateProject(projectId: number, projectData: ProjectUpdateForm): Promise<Project> {
  return request.put<Project>(`/projects/${projectId}`, projectData)
}

/**
 * 删除项目 API
 * @param projectId 项目 ID
 * @returns void
 */
export function deleteProject(projectId: number): Promise<void> {
  return request.delete<void>(`/projects/${projectId}`)
}

/**
 * 同步项目用例 API
 * @param projectId 项目 ID
 * @returns void
 */
export function syncProject(projectId: number): Promise<void> {
  return request.post<void>(`/projects/${projectId}/sync`)
}
