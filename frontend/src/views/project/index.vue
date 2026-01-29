<template>
  <div class="project-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>项目管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建项目
      </el-button>
    </div>

    <!-- 项目列表 - 卡片布局 -->
    <div v-loading="loading" class="project-list">
      <el-empty 
        v-if="!loading && projectStore.projects.length === 0" 
        description="暂无项目，请创建一个项目开始使用" 
      />
      
      <el-row v-else :gutter="24">
        <el-col 
          v-for="project in projectStore.projects" 
          :key="project.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <el-card class="project-card" shadow="never" :body-style="{ padding: '24px' }">
            <!-- 项目名称 -->
            <template #header>
              <div class="card-header">
                <span class="project-name">{{ project.name }}</span>
              </div>
            </template>

            <!-- 项目描述 -->
            <div class="card-body">
              <p class="project-description">
                {{ project.description || '暂无描述' }}
              </p>
              <div v-if="project.git_url" class="project-git">
                <el-icon><Link /></el-icon>
                <span class="git-url" :title="project.git_url">
                  {{ truncateGitUrl(project.git_url) }}
                </span>
                <el-tag v-if="project.git_branch" size="small" type="info">
                  {{ project.git_branch }}
                </el-tag>
              </div>
              <p class="project-time">
                创建于: {{ formatDate(project.created_at) }}
              </p>
            </div>

            <!-- 操作按钮 -->
            <template #footer>
              <div class="card-footer">
                <el-button 
                  type="primary" 
                  size="small"
                  @click="handleEnterProject(project)"
                >
                  进入项目
                </el-button>
                <el-button 
                  v-if="project.git_url"
                  type="success" 
                  size="small"
                  :loading="syncingProjectId === project.id"
                  @click="handleSync(project)"
                >
                  同步用例
                </el-button>
                <el-button 
                  type="danger" 
                  size="small"
                  @click="handleDelete(project)"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 创建项目弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="新建项目"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入项目名称"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="Git 仓库" prop="git_url">
          <el-input
            v-model="form.git_url"
            placeholder="https://github.com/user/repo.git"
            clearable
          />
        </el-form-item>
        <el-form-item label="Git 分支" prop="git_branch">
          <el-input
            v-model="form.git_branch"
            placeholder="main"
            clearable
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { syncProject } from '@/api/project'
import { useProjectStore } from '@/stores/project'
import type { Project, ProjectCreate } from '@/types/project'
import { Link, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const projectStore = useProjectStore()

// 加载状态
const loading = ref(false)

// 弹窗状态
const dialogVisible = ref(false)
const submitting = ref(false)

// 同步状态 (记录当前正在同步的项目 ID)
const syncingProjectId = ref<number | null>(null)

// 表单引用和数据
const formRef = ref<FormInstance>()
const form = ref<ProjectCreate>({
  name: '',
  description: '',
  git_url: '',
  git_branch: 'main',
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 255, message: '项目名称长度在 1 到 255 个字符', trigger: 'blur' },
  ],
}

/**
 * 格式化日期
 */
function formatDate(dateStr: string): string {
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
 * 截断 Git URL 以便显示
 */
function truncateGitUrl(url: string): string {
  if (url.length <= 40) return url
  return url.slice(0, 37) + '...'
}

/**
 * 加载项目列表
 */
async function loadProjectList() {
  loading.value = true
  try {
    await projectStore.loadProjects()
  } catch (error) {
    console.error('Failed to load projects:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 打开创建项目弹窗
 */
function handleCreate() {
  // 重置表单
  form.value = {
    name: '',
    description: '',
    git_url: '',
    git_branch: 'main',
  }
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

/**
 * 提交创建项目表单
 */
async function handleSubmit() {
  if (!formRef.value) return

  // 表单验证
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    // 调用 store action 创建项目
    await projectStore.create(form.value)
    
    // 关闭弹窗
    dialogVisible.value = false
  } catch (error) {
    console.error('Failed to create project:', error)
  } finally {
    submitting.value = false
  }
}

/**
 * 进入项目
 */
function handleEnterProject(project: Project) {
  // 设置当前项目
  projectStore.selectProject(project.id)
  
  // 跳转到 Dashboard
  router.push('/dashboard')
  
  ElMessage.success(`已进入项目: ${project.name}`)
}

/**
 * 同步项目用例
 */
async function handleSync(project: Project) {
  syncingProjectId.value = project.id
  try {
    await syncProject(project.id)
    ElMessage.success('同步任务已触发')
  } catch (error) {
    console.error('Failed to sync project:', error)
    ElMessage.error('同步任务触发失败')
  } finally {
    syncingProjectId.value = null
  }
}

/**
 * 删除项目
 */
async function handleDelete(project: Project) {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？此操作不可恢复。`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    // 调用 store action 删除项目
    await projectStore.deleteProject(project.id)
  } catch (error) {
    // 用户取消删除
    if (error === 'cancel') {
      return
    }
    console.error('Failed to delete project:', error)
  }
}

// 组件挂载时加载项目列表
onMounted(() => {
  loadProjectList()
})
</script>

<style scoped lang="scss">
.project-container {
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  h2 {
    margin: 0;
    font-size: 32px;
    font-weight: 600;
    color: #1d1d1f;
  }
}

.project-list {
  min-height: 400px;
}

.project-card {
  margin-bottom: 24px;
  border: none;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
  }

  :deep(.el-card__header) {
    border-bottom: none;
    padding: 24px 24px 0 24px;
  }
  
  // body padding is set via prop

  :deep(.el-card__footer) {
    border-top: none;
    padding: 0 24px 24px 24px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .project-name {
      font-size: 20px;
      font-weight: 600;
      color: #1d1d1f;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .card-body {
    min-height: 100px;

    .project-description {
      color: #86868b;
      font-size: 15px;
      line-height: 1.5;
      margin: 8px 0 16px 0;
      min-height: 44px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .project-git {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 8px;
      color: #0071e3;
      font-size: 13px;

      .git-url {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        cursor: pointer;
        
        &:hover {
          text-decoration: underline;
        }
      }
    }

    .project-time {
      color: #86868b;
      font-size: 13px;
      margin: 0;
    }
  }

  .card-footer {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 16px;

    .el-button {
      flex: 1;
      min-width: 80px;
      border-radius: 8px;
    }
  }
}
</style>
