<script setup lang="ts">
/**
 * 主布局组件
 * 包含头部导航、侧边栏和内容区域
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)

function toggleSidebar() {
  isCollapse.value = !isCollapse.value
}

/**
 * 处理下拉菜单命令
 */
function handleCommand(command: string) {
  if (command === 'logout') {
    handleLogout()
  }
}

/**
 * 退出登录
 */
function handleLogout() {
  userStore.logout()
}
</script>

<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
      <div class="logo">
        <h2 v-if="!isCollapse">ATP Platform</h2>
        <h2 v-else>ATP</h2>
      </div>
      
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <el-menu-item index="/home">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        
        <el-menu-item index="/about">
          <el-icon><InfoFilled /></el-icon>
          <template #title>关于</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-button :icon="isCollapse ? 'Expand' : 'Fold'" @click="toggleSidebar" />
          <span class="header-title">ATP Platform</span>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ userStore.userInfo?.username || userStore.userInfo?.email || '用户' }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  transition: width 0.3s;
  
  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 60px;
    background-color: #2b3a4b;
    
    h2 {
      margin: 0;
      color: #fff;
      font-size: 24px;
      font-weight: bold;
    }
  }
  
  .sidebar-menu {
    border-right: none;
    background-color: #304156;
  }
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  
  .header-left {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 16px;
    
    .header-title {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 0 12px;
      height: 40px;
      border-radius: 4px;
      transition: background-color 0.3s;
      
      &:hover {
        background-color: #f5f7fa;
      }
    }
  }
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
