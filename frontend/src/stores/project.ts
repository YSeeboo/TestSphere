/**
 * 项目状态管理 Store
 * 使用 Pinia Setup Syntax
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import type { AxiosError } from 'axios'
import { getProjects, createProject as createProjectApi, deleteProject as deleteProjectApi, syncProject as syncProjectApi } from '@/api/project'
import type { Project, ProjectCreate } from '@/types/project'
import type { ApiErrorResponse } from '@/utils/request'
import { eventBus } from '@/utils/eventBus'

const ACTIVE_PROJECT_KEY = 'active_project_id'

/**
 * 从 localStorage 初始化项目 ID
 */
function initProjectIdFromStorage(): number | null {
  const saved = localStorage.getItem(ACTIVE_PROJECT_KEY)
  if (saved) {
    const id = parseInt(saved, 10)
    return isNaN(id) ? null : id
  }
  return null
}

/**
 * 项目 Store
 */
export const useProjectStore = defineStore('project', () => {
  // State: 项目列表
  const projects = ref<Project[]>([])

  // State: 当前选中的项目 ID（直接从 localStorage 初始化）
  const currentProjectId = ref<number | null>(initProjectIdFromStorage())

  // Getter: 当前选中的项目对象
  const currentProject = computed(() => {
    if (!currentProjectId.value) return null
    return projects.value.find(p => p.id === currentProjectId.value) || null
  })

  // 监听用户登出事件，清理项目状态
  eventBus.on('user:logout', () => {
    reset()
  })

  /**
   * 选择项目 - 设置 currentProjectId 并存入 localStorage
   * @param id 项目 ID (null 表示清除当前项目)
   */
  function selectProject(id: number | null) {
    currentProjectId.value = id
    if (id !== null) {
      localStorage.setItem(ACTIVE_PROJECT_KEY, id.toString())
      eventBus.emit('project:change', { projectId: id })
    } else {
      localStorage.removeItem(ACTIVE_PROJECT_KEY)
    }
  }

  /**
   * 加载项目列表
   * @returns Promise<void>
   */
  async function loadProjects(): Promise<void> {
    try {
      const projectList = await getProjects()
      projects.value = projectList

      // 如果当前项目 ID 不在列表中，清除它
      if (currentProjectId.value) {
        const exists = projectList.some(p => p.id === currentProjectId.value)
        if (!exists) {
          selectProject(null)
        }
      }
    } catch (error) {
      console.error('Failed to load projects:', error)
      const axiosError = error as AxiosError<ApiErrorResponse>
      const errorMessage = axiosError.response?.data?.detail || '获取项目列表失败'
      ElMessage.error(errorMessage)
      throw error
    }
  }

  /**
   * 创建项目
   * @param data 项目创建数据
   * @returns Promise<Project>
   */
  async function create(data: ProjectCreate): Promise<Project> {
    try {
      const newProject = await createProjectApi(data)

      // 重新加载项目列表
      await loadProjects()

      ElMessage.success('项目创建成功')
      return newProject
    } catch (error) {
      console.error('Failed to create project:', error)
      const axiosError = error as AxiosError<ApiErrorResponse>
      const errorMessage = axiosError.response?.data?.detail || '创建项目失败'
      ElMessage.error(errorMessage)
      throw error
    }
  }

  /**
   * 删除项目
   * @param projectId 项目 ID
   * @returns Promise<void>
   */
  async function deleteProject(projectId: number): Promise<void> {
    try {
      await deleteProjectApi(projectId)

      // 从列表中移除
      projects.value = projects.value.filter(p => p.id !== projectId)

      // 如果删除的是当前项目，清除当前项目
      if (currentProjectId.value === projectId) {
        selectProject(null)
      }

      ElMessage.success('项目删除成功')
    } catch (error) {
      console.error('Failed to delete project:', error)
      const axiosError = error as AxiosError<ApiErrorResponse>
      const errorMessage = axiosError.response?.data?.detail || '删除项目失败'
      ElMessage.error(errorMessage)
      throw error
    }
  }

  /**
   * 同步项目测试用例
   * @param projectId 项目 ID
   * @returns Promise<void>
   */
  async function syncProject(projectId: number): Promise<void> {
    try {
      await syncProjectApi(projectId)
      ElMessage.success('同步任务已提交')
      eventBus.emit('project:sync', { projectId })
    } catch (error) {
      console.error('Failed to sync project:', error)
      const axiosError = error as AxiosError<ApiErrorResponse>
      const errorMessage = axiosError.response?.data?.detail || '同步项目失败'
      ElMessage.error(errorMessage)
      throw error
    }
  }

  /**
   * 重置 Store 状态
   */
  function reset() {
    projects.value = []
    selectProject(null)
  }

  return {
    // State
    projects,
    currentProjectId,

    // Getters
    currentProject,

    // Actions
    selectProject,
    loadProjects,
    create,
    deleteProject,
    syncProject,
    reset,
  }
})
