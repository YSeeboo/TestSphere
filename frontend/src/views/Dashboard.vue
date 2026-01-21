<script setup lang="ts">
/**
 * 仪表盘页面 - 简单的欢迎页面
 */
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 获取用户显示名称（优先显示 email）
const displayName = computed(() => {
  return userStore.userInfo?.email || userStore.userInfo?.username || '用户'
})
</script>

<template>
  <div class="dashboard-container">
    <el-card class="welcome-card">
      <div class="welcome-content">
        <el-icon class="welcome-icon"><UserFilled /></el-icon>
        <h1>欢迎, {{ displayName }}</h1>
        <p class="welcome-text">您已成功登录 ATP Platform 自动化测试平台</p>
        <el-divider />
        <div class="info-section">
          <p><strong>用户信息：</strong></p>
          <ul>
            <li>邮箱: {{ userStore.userInfo?.email }}</li>
            <li>用户名: {{ userStore.userInfo?.username }}</li>
            <li>
              账户类型: 
              <el-tag :type="userStore.isSuperUser ? 'danger' : 'success'" size="small">
                {{ userStore.isSuperUser ? '超级管理员' : '普通用户' }}
              </el-tag>
            </li>
          </ul>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.dashboard-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 120px);
  
  .welcome-card {
    max-width: 600px;
    width: 100%;
    
    .welcome-content {
      text-align: center;
      padding: 40px 20px;
      
      .welcome-icon {
        font-size: 80px;
        color: #409eff;
        margin-bottom: 20px;
      }
      
      h1 {
        margin: 0 0 16px 0;
        color: #303133;
        font-size: 32px;
        font-weight: 600;
      }
      
      .welcome-text {
        color: #606266;
        font-size: 16px;
        margin-bottom: 30px;
      }
      
      .info-section {
        text-align: left;
        margin-top: 20px;
        
        p {
          margin: 10px 0;
          color: #303133;
          font-size: 16px;
        }
        
        ul {
          list-style: none;
          padding: 0;
          margin: 10px 0;
          
          li {
            padding: 8px 0;
            color: #606266;
            font-size: 14px;
            border-bottom: 1px solid #f0f0f0;
            
            &:last-child {
              border-bottom: none;
            }
          }
        }
      }
    }
  }
}
</style>
