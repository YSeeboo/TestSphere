/**
 * 项目相关的 TypeScript 类型定义
 */

/**
 * 项目信息接口
 */
export interface Project {
  id: number
  name: string
  description: string | null
  owner_id: number
  git_url: string | null
  git_branch: string
  last_sync_time: string | null
  last_sync_status: string
  created_at: string
  updated_at: string
}

/**
 * 项目创建数据
 */
export interface ProjectCreate {
  name: string
  description?: string
  git_url?: string
  git_branch?: string
}

/**
 * 项目创建表单 (别名，保持向后兼容)
 */
export type ProjectCreateForm = ProjectCreate

/**
 * 项目更新表单
 */
export interface ProjectUpdateForm {
  name?: string
  description?: string
  git_url?: string
  git_branch?: string
}
