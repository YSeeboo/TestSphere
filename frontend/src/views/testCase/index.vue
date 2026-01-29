<script setup lang="ts">
/**
 * 用例管理页面
 * 展示当前项目的测试用例列表，支持分页和同步功能
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, DocumentCopy } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { getTestCases } from '@/api/testCase'
import { runTest } from '@/api/execution'
import type { TestCase } from '@/types/testCase'

const router = useRouter()
const projectStore = useProjectStore()

// 表格数据
const testCases = ref<TestCase[]>([])
const loading = ref(false)
const total = ref(0)

// 分页参数
const pageSize = ref(20)
const currentPage = ref(1)

// 计算偏移量
const offset = computed(() => (currentPage.value - 1) * pageSize.value)

// 是否正在同步
const syncing = ref(false)

// 是否正在运行测试
const running = ref(false)

/**
 * 加载测试用例列表
 */
async function loadTestCases() {
  const projectId = projectStore.currentProjectId
  if (!projectId) {
    ElMessage.warning('请先选择项目')
    return
  }

  loading.value = true
  try {
    const response = await getTestCases(projectId, {
      limit: pageSize.value,
      offset: offset.value,
    })
    testCases.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('加载测试用例失败:', error)
    ElMessage.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

/**
 * 同步项目测试用例
 */
async function handleSync() {
  const projectId = projectStore.currentProjectId
  if (!projectId) {
    ElMessage.warning('请先选择项目')
    return
  }

  try {
    await ElMessageBox.confirm(
      '同步将从 Git 仓库拉取最新代码并收集测试用例，可能需要一些时间。是否继续？',
      '确认同步',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    syncing.value = true
    await projectStore.syncProject(projectId)
    ElMessage.success('同步任务已提交，3秒后将自动刷新列表')

    // 3秒后自动刷新列表
    setTimeout(() => {
      loadTestCases()
      syncing.value = false
    }, 3000)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('同步失败:', error)
      ElMessage.error('同步失败')
      syncing.value = false
    }
  }
}

/**
 * 运行测试
 */
async function handleRunTest() {
  const projectId = projectStore.currentProjectId
  if (!projectId) {
    ElMessage.warning('请先选择项目')
    return
  }

  try {
    await ElMessageBox.confirm(
      '将使用默认配置运行测试 (env=dev)。是否继续？',
      '确认运行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    running.value = true
    const response = await runTest(projectId, { env: 'dev' })
    const executionId = response.id ?? response.execution_id
    
    if (!executionId) {
      ElMessage.error('未获取到执行 ID')
      return
    }
    
    ElMessage.success('测试已启动')
    router.push(`/executions/${executionId}`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('运行测试失败:', error)
      ElMessage.error('运行测试失败')
    }
  } finally {
    running.value = false
  }
}

/**
 * 处理分页大小变化
 */
function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadTestCases()
}

/**
 * 处理页码变化
 */
function handleCurrentChange(page: number) {
  currentPage.value = page
  loadTestCases()
}

/**
 * 格式化 markers 为标签数组
 * markers 可能是 null 或者 { "marker_name": {...}, ... }
 */
function formatMarkers(markers: Record<string, any> | null): string[] {
  if (!markers) return []
  return Object.keys(markers)
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

/**
 * 监听项目切换，重新加载数据
 */
watch(
  () => projectStore.currentProjectId,
  (newId) => {
    if (newId) {
      currentPage.value = 1
      loadTestCases()
    } else {
      testCases.value = []
      total.value = 0
    }
  },
  { immediate: true }
)

onMounted(() => {
  loadTestCases()
})
</script>

<template>
  <div class="test-case-container">
    <!-- 标题栏 -->
    <div class="header">
      <div class="header-left">
        <el-icon :size="24"><DocumentCopy /></el-icon>
        <h2>用例管理</h2>
        <span class="subtitle">当前项目: {{ projectStore.currentProject?.name || '未选择' }}</span>
      </div>
      <div class="header-right">
        <el-button
          type="primary"
          :icon="Refresh"
          :loading="syncing"
          @click="handleSync"
        >
          {{ syncing ? '同步中...' : '同步用例' }}
        </el-button>
        <el-button type="primary" :loading="running" @click="handleRunTest">
          {{ running ? '运行中...' : '运行测试' }}
        </el-button>
        <el-button :icon="Refresh" @click="loadTestCases">刷新</el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats">
      <el-card shadow="hover">
        <div class="stat-item">
          <span class="stat-label">测试用例总数</span>
          <span class="stat-value">{{ total }}</span>
        </div>
      </el-card>
    </div>

    <!-- 测试用例表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        :data="testCases"
        :loading="loading"
        stripe
        border
        style="width: 100%"
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        
        <el-table-column prop="name" label="测试名称" min-width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.nodeid" placement="top">
              <span class="test-name">{{ row.name }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        
        <el-table-column prop="file_path" label="文件路径" min-width="250">
          <template #default="{ row }">
            <el-text type="info" size="small">{{ row.file_path }}</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            <span v-if="row.description">{{ row.description }}</span>
            <el-text v-else type="info" size="small">无描述</el-text>
          </template>
        </el-table-column>
        
        <el-table-column label="Markers" min-width="180">
          <template #default="{ row }">
            <div class="markers-container">
              <el-tag
                v-for="marker in formatMarkers(row.markers)"
                :key="marker"
                size="small"
                type="info"
                effect="plain"
              >
                {{ marker }}
              </el-tag>
              <el-text v-if="!formatMarkers(row.markers).length" type="info" size="small">
                无
              </el-text>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <el-text size="small">{{ formatDateTime(row.created_at) }}</el-text>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.test-case-container {
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
    
    .header-right {
      display: flex;
      gap: 12px;
    }
  }
  
  .stats {
    margin-bottom: 20px;
    
    .stat-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 16px;
      
      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-bottom: 8px;
      }
      
      .stat-value {
        font-size: 32px;
        font-weight: 600;
        color: #409eff;
      }
    }
  }
  
  .table-card {
    .test-name {
      font-weight: 500;
      color: #303133;
      cursor: help;
    }
    
    .markers-container {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    
    .pagination {
      display: flex;
      justify-content: flex-end;
      margin-top: 20px;
    }
  }
}
</style>
