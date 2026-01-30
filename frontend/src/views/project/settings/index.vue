<template>
  <div class="cron-settings">
    <div class="page-header">
      <h2>定时任务</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建任务
      </el-button>
    </div>

    <el-card v-loading="loading" shadow="never">
      <el-table :data="jobs" style="width: 100%">
        <el-table-column prop="name" label="任务名" min-width="160" />
        <el-table-column prop="cron_expression" label="Cron 表达式" min-width="160" />
        <el-table-column label="开关" width="120">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              :loading="switchingJobId === row.id"
              @change="toggleJob(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="上次执行" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.last_run_at) }}</template>
        </el-table-column>
        <el-table-column label="下次执行" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.next_run_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="success" @click="runNow(row)">立即执行</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="任务名" prop="name">
          <el-input v-model="form.name" placeholder="例如：每日回归" />
        </el-form-item>
        <el-form-item label="Cron 表达式" prop="cron_expression">
          <el-input v-model="form.cron_expression" placeholder="例如：0 2 * * *" />
        </el-form-item>
        <el-form-item label="环境" prop="env">
          <el-input v-model="form.env" placeholder="例如：staging" />
        </el-form-item>
        <el-form-item label="Marker" prop="marker_expression">
          <el-input v-model="form.marker_expression" placeholder="例如：smoke and not slow" />
        </el-form-item>
        <el-form-item label="Keyword" prop="keyword_expression">
          <el-input v-model="form.keyword_expression" placeholder="例如：login or logout" />
        </el-form-item>
        <el-form-item label="启用" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { createCronJob, deleteCronJob, getCronJobs, runCronJobNow, updateCronJob, type CronJob } from '@/api/cronJob'
import { useProjectStore } from '@/stores/project'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const projectStore = useProjectStore()

const loading = ref(false)
const jobs = ref<CronJob[]>([])
const dialogVisible = ref(false)
const submitting = ref(false)
const editingJob = ref<CronJob | null>(null)
const switchingJobId = ref<number | null>(null)

const formRef = ref<FormInstance>()
const form = ref({
  name: '',
  cron_expression: '',
  env: '',
  marker_expression: '',
  keyword_expression: '',
  is_active: true,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入任务名', trigger: 'blur' }],
  cron_expression: [{ required: true, message: '请输入 Cron 表达式', trigger: 'blur' }],
}

const projectId = computed(() => {
  const fromRoute = Number(route.params.projectId)
  if (!Number.isNaN(fromRoute) && fromRoute > 0) return fromRoute
  return projectStore.currentProjectId || 0
})

const dialogTitle = computed(() => (editingJob.value ? '编辑任务' : '新建任务'))

function formatDateTime(dateStr?: string | null): string {
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

async function loadJobs() {
  if (!projectId.value) {
    ElMessage.error('未选择项目')
    return
  }
  loading.value = true
  try {
    jobs.value = await getCronJobs(projectId.value)
  } catch (error) {
    console.error('加载定时任务失败:', error)
    ElMessage.error('加载定时任务失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  editingJob.value = null
  form.value = {
    name: '',
    cron_expression: '',
    env: '',
    marker_expression: '',
    keyword_expression: '',
    is_active: true,
  }
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

function openEditDialog(job: CronJob) {
  editingJob.value = job
  form.value = {
    name: job.name,
    cron_expression: job.cron_expression,
    env: job.env || '',
    marker_expression: job.marker_expression || '',
    keyword_expression: job.keyword_expression || '',
    is_active: job.is_active,
  }
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value || !projectId.value) return
  await formRef.value.validate()

  submitting.value = true
  try {
    if (editingJob.value) {
      await updateCronJob(projectId.value, editingJob.value.id, { ...form.value })
      ElMessage.success('任务已更新')
    } else {
      await createCronJob(projectId.value, { ...form.value })
      ElMessage.success('任务已创建')
    }
    dialogVisible.value = false
    await loadJobs()
  } catch (error) {
    console.error('保存任务失败:', error)
    ElMessage.error('保存任务失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(job: CronJob) {
  if (!projectId.value) return
  try {
    await ElMessageBox.confirm(`确认删除任务「${job.name}」吗？`, '提示', {
      type: 'warning',
    })
    await deleteCronJob(projectId.value, job.id)
    ElMessage.success('任务已删除')
    await loadJobs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除任务失败')
    }
  }
}

async function toggleJob(job: CronJob) {
  if (!projectId.value) return
  switchingJobId.value = job.id
  try {
    await updateCronJob(projectId.value, job.id, { is_active: job.is_active })
    ElMessage.success(job.is_active ? '已启用' : '已停用')
  } catch (error) {
    job.is_active = !job.is_active
    console.error('更新任务状态失败:', error)
    ElMessage.error('更新任务状态失败')
  } finally {
    switchingJobId.value = null
  }
}

async function runNow(job: CronJob) {
  if (!projectId.value) return
  try {
    await runCronJobNow(projectId.value, job.id)
    ElMessage.success(`已触发执行：${job.name}`)
  } catch (error) {
    console.error('触发执行失败:', error)
    ElMessage.error('触发执行失败')
  }
}

onMounted(() => {
  loadJobs()
})
</script>

<style scoped lang="scss">
.cron-settings {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      font-size: 22px;
      font-weight: 600;
      color: #303133;
    }
  }
}
</style>
