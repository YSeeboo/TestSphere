<script setup lang="ts">
/**
 * 执行详情页面 (带轮询)
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Refresh, Tickets } from '@element-plus/icons-vue'
import { getExecutionDetail } from '@/api/execution'
import type { ExecutionDetail } from '@/api/execution'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const execution = ref<ExecutionDetail | null>(null)
const loading = ref(false)
let pollingTimer: number | null = null

const executionId = computed(() => Number(route.params.id))

/**
 * 判断是否需要轮询
 */
function shouldPoll(status?: string): boolean {
  return status === 'pending' || status === 'running'
}

/**
 * 判断是否终止状态
 */
function isTerminal(status?: string): boolean {
  return status === 'success' || status === 'failed' || status === 'error'
}

/**
 * 获取执行详情
 */
async function loadExecutionDetail() {
  if (!executionId.value || Number.isNaN(executionId.value)) {
    ElMessage.error('无效的执行 ID')
    return
  }

  loading.value = true
  try {
    const detail = await getExecutionDetail(executionId.value)
    execution.value = detail
    
    if (shouldPoll(detail.status)) {
      startPolling()
    } else if (isTerminal(detail.status)) {
      stopPolling()
    }
  } catch (error) {
    console.error('加载执行详情失败:', error)
    ElMessage.error('加载执行详情失败')
  } finally {
    loading.value = false
  }
}

/**
 * 开始轮询
 */
function startPolling() {
  if (pollingTimer !== null) return
  pollingTimer = window.setInterval(() => {
    loadExecutionDetail()
  }, 2000)
}

/**
 * 停止轮询
 */
function stopPolling() {
  if (pollingTimer !== null) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

/**
 * 返回列表
 */
function goBack() {
  if (projectStore.currentProjectId) {
    router.push(`/projects/${projectStore.currentProjectId}/executions`)
  } else {
    router.push('/projects')
  }
}

/**
 * 状态展示样式
 */
function getStatusType(status: string | undefined): 'success' | 'danger' | 'warning' | 'info' {
  if (status === 'success') return 'success'
  if (status === 'failed' || status === 'error') return 'danger'
  if (status === 'running') return 'warning'
  return 'info'
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadExecutionDetail()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="execution-detail-container">
    <!-- 标题栏 -->
    <div class="header">
      <div class="header-left">
        <el-icon :size="24"><Tickets /></el-icon>
        <h2>执行详情</h2>
        <el-tag v-if="execution" :type="getStatusType(execution.status)" size="small">
          {{ execution.status }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button :icon="ArrowLeft" @click="goBack">返回列表</el-button>
        <el-button :icon="Refresh" @click="loadExecutionDetail">刷新</el-button>
      </div>
    </div>

    <el-card v-loading="loading" class="detail-card" shadow="never">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="执行 ID">
          {{ execution?.id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="触发方式">
          <el-tag type="info" size="small" effect="plain">
            {{ execution?.trigger_type || '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(execution?.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="轮询状态">
          <el-tag v-if="execution && shouldPoll(execution.status)" type="warning" size="small">
            轮询中
          </el-tag>
          <el-tag v-else type="info" size="small">已停止</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div class="log-section">
        <div class="log-title">执行日志</div>
        <pre class="log-content">{{ execution?.logs || '暂无日志' }}</pre>
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.execution-detail-container {
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
      
      h2 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
        color: #303133;
      }
    }
  }
  
  .detail-card {
    .log-section {
      margin-top: 20px;
      
      .log-title {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 10px;
      }
      
      .log-content {
        margin: 0;
        padding: 16px;
        background: #000;
        color: #4cff7a;
        border-radius: 4px;
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        font-size: 13px;
        line-height: 1.6;
        max-height: 520px;
        overflow: auto;
        white-space: pre-wrap;
        word-break: break-word;
      }
    }
  }
}
</style>
