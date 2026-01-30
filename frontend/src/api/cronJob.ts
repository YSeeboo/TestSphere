/**
 * Cron 任务相关 API
 */

import request from '@/utils/request'

export interface CronJob {
  id: number
  project_id: number
  name: string
  cron_expression: string
  is_active: boolean
  env: string | null
  marker_expression: string | null
  keyword_expression: string | null
  last_run_at: string | null
  next_run_at: string | null
  created_at: string
  updated_at: string
}

export interface CronJobCreate {
  name: string
  cron_expression: string
  is_active: boolean
  env?: string
  marker_expression?: string
  keyword_expression?: string
}

export interface CronJobUpdate {
  name?: string
  cron_expression?: string
  is_active?: boolean
  env?: string
  marker_expression?: string
  keyword_expression?: string
}

export function getCronJobs(projectId: number): Promise<CronJob[]> {
  return request.get<CronJob[]>(`/projects/${projectId}/cron-jobs`)
}

export function createCronJob(projectId: number, payload: CronJobCreate): Promise<CronJob> {
  return request.post<CronJob>(`/projects/${projectId}/cron-jobs`, payload)
}

export function updateCronJob(
  projectId: number,
  jobId: number,
  payload: CronJobUpdate,
): Promise<CronJob> {
  return request.put<CronJob>(`/projects/${projectId}/cron-jobs/${jobId}`, payload)
}

export function deleteCronJob(projectId: number, jobId: number): Promise<void> {
  return request.delete<void>(`/projects/${projectId}/cron-jobs/${jobId}`)
}

export function runCronJobNow(projectId: number, jobId: number): Promise<Record<string, unknown>> {
  return request.post(`/projects/${projectId}/cron-jobs/${jobId}/run`)
}
