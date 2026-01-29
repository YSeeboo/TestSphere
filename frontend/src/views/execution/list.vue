<script setup lang="ts">
/**
 * 执行记录列表页面
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Tickets } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { getProjectExecutions } from '@/api/execution'
import type { ExecutionList } from '@/api/execution'

const router = useRouter()
const projectStore = useProjectStore()

const executions = ref<ExecutionList[]>([])
const loading = ref(false)

const currentProjectName = computed(() => {
  return projectStore.currentProject?.name || '未选择项目'
})

/**
 * 获取执行记录列表
 */
async function loadExecutions() {
  const projectId = projectStore.currentProjectId
  if (!projectId) {
    executions.value = []
    ElMessage.warning('请先选择项目')
    return
  }

  loading.value = true
  try {
    executions.value = await getProjectExecutions(projectId)
  } catch (error) {
    console.error('加载执行记录失败:', error)
    ElMessage.error('加载执行记录失败')
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到执行详情
 */
function goToDetail(executionId: number) {
  router.push(`/executions/${executionId}`)
}

/**
 * 状态展示样式
 */
function getStatusType(status: string): 'success' | 'danger' | 'warning' | 'info' {
  if (status === 'success') return 'success'
  if (status === 'failed' || status === 'error') return 'danger'
  if (status === 'running') return 'warning'
  return 'info'
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

watch(
  () => projectStore.currentProjectId,
  (newId) => {
    if (newId) {
      loadExecutions()
    } else {
      executions.value = []
    }
  },
  { immediate: true }
)

onMounted(() => {
  loadExecutions()
})
</script>

<template>
  <div class="execution-list-container">
    <!-- 标题栏 -->
    <div class="header">
      <div class="header-left">
        <el-icon :size="24"><Tickets /></el-icon>
        <h2>执行记录</h2>
        <span class="subtitle">当前项目: {{ currentProjectName }}</span>
      </div>
      <div class="header-right">
        <el-button :icon="Refresh" @click="loadExecutions">刷新</el-button>
      </div>
    </div>

    <el-card class="table-card" shadow="never">
      <el-table
        :data="executions"
        :loading="loading"
        stripe
        border
        style="width: 100%"
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#606266' }"
        @row-click="(row) => goToDetail(row.id)"
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        
        <el-table-column prop="id" label="执行 ID" width="120" />
        
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="trigger_type" label="触发方式" width="140">
          <template #default="{ row }">
            <el-tag type="info" size="small" effect="plain">{{ row.trigger_type }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" min-width="180">
          <template #default="{ row }">
            <el-text size="small">{{ formatDateTime(row.created_at) }}</el-text>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="goToDetail(row.id)">
              查看日志
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && executions.length === 0"
        description="暂无执行记录"
        :image-size="80"
        class="empty-state"
      />
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.execution-list-container {
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
      
      .subtitle {
        font-size: 14px;
        color: #909399;
        margin-left: 8px;
      }
    }
  }
  
  .table-card {
    .empty-state {
      margin: 20px 0;
    }
  }
}
</style>
