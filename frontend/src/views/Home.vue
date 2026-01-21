<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getHealth, type HealthResponse } from '@/api/health'

const loading = ref(false)
const healthData = ref<HealthResponse | null>(null)

// 获取健康状态
const fetchHealth = async () => {
  loading.value = true
  try {
    const data = await getHealth()
    healthData.value = data
    ElMessage.success('健康检查成功')
  } catch (error) {
    ElMessage.error('健康检查失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchHealth()
})
</script>

<template>
  <div class="home-container">
    <el-card class="welcome-card">
      <template #header>
        <div class="card-header">
          <span class="title">🚀 欢迎使用 ATP 自动化测试平台</span>
        </div>
      </template>

      <div class="content">
        <el-alert
          title="系统提示"
          type="info"
          description="这是一个自动化测试平台的前端界面，基于 Vue 3 + TypeScript + Element Plus 构建。"
          :closable="false"
          style="margin-bottom: 20px"
        />

        <el-divider content-position="left">后端健康状态</el-divider>

        <el-button type="primary" @click="fetchHealth" :loading="loading">
          <el-icon><Refresh /></el-icon>
          <span>刷新健康状态</span>
        </el-button>

        <div v-if="healthData" class="health-info">
          <el-descriptions :column="2" border style="margin-top: 20px">
            <el-descriptions-item label="服务状态">
              <el-tag :type="healthData.status === 'healthy' ? 'success' : 'danger'">
                {{ healthData.status }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="服务名称">
              {{ healthData.service }}
            </el-descriptions-item>
            <el-descriptions-item label="版本">
              {{ healthData.version }}
            </el-descriptions-item>
            <el-descriptions-item label="数据库">
              <el-tag :type="healthData.database === 'connected' ? 'success' : 'danger'">
                {{ healthData.database }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Redis">
              <el-tag :type="healthData.redis === 'connected' ? 'success' : 'danger'">
                {{ healthData.redis }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <el-divider content-position="left">快速开始</el-divider>

        <el-space direction="vertical" :size="10" style="width: 100%">
          <el-card shadow="hover">
            <h3>📖 查看文档</h3>
            <p>访问 <a href="http://localhost:8000/api/v1/docs" target="_blank">Swagger API 文档</a></p>
          </el-card>

          <el-card shadow="hover">
            <h3>🔧 开发指南</h3>
            <p>查看项目根目录的 <code>QUICKSTART.md</code> 和 <code>.cursorrules</code></p>
          </el-card>

          <el-card shadow="hover">
            <h3>📊 技术栈</h3>
            <ul>
              <li>前端: Vue 3 + TypeScript + Vite + Element Plus + Pinia</li>
              <li>后端: Python 3.11 + FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis</li>
            </ul>
          </el-card>
        </el-space>
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.home-container {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .welcome-card {
    max-width: 1200px;
    margin: 0 auto;

    .card-header {
      .title {
        font-size: 24px;
        font-weight: bold;
      }
    }

    .content {
      h3 {
        margin-top: 0;
        color: #409eff;
      }

      p {
        margin: 10px 0;
        line-height: 1.6;
      }

      ul {
        margin: 10px 0;
        padding-left: 20px;

        li {
          line-height: 2;
        }
      }

      code {
        padding: 2px 6px;
        background: #f5f7fa;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
      }

      a {
        color: #409eff;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
      }
    }
  }
}
</style>
