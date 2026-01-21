<script setup lang="ts">
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getHealth } from '@/api/health'

// 组件挂载时检查后端健康状态
onMounted(async () => {
  try {
    const health = await getHealth()
    console.log('Backend Health:', health)
    if (health.status === 'healthy') {
      ElMessage.success(`连接到后端成功: ${health.service} v${health.version}`)
    }
  } catch (error) {
    console.error('Backend health check failed:', error)
    ElMessage.warning('无法连接到后端服务，请确保后端已启动')
  }
})
</script>

<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style scoped>
#app {
  width: 100%;
  height: 100%;
}
</style>
