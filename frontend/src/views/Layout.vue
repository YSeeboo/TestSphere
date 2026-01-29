<script setup lang="ts">
/**
 * 主布局组件
 * 包含头部导航、侧边栏和内容区域
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Folder, DataAnalysis, HomeFilled, InfoFilled, User, DocumentCopy, Tickets } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useProjectStore } from '@/stores/project'

const router = useRouter()
const userStore = useUserStore()
const projectStore = useProjectStore()

// 当前项目名称
const currentProjectName = computed(() => {
  return projectStore.currentProject?.name || '未选择项目'
})

// 是否已选择项目
const hasProject = computed(() => {
  return projectStore.currentProjectId !== null
})

// 执行记录路径
const executionListPath = computed(() => {
  if (!projectStore.currentProjectId) return '/projects'
  return `/projects/${projectStore.currentProjectId}/executions`
})

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

// 注意：projectStore 现在会在定义时自动从 localStorage 初始化
// 不再需要手动调用 init() 方法
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
        <!-- 项目管理 - 始终显示 -->
        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <template #title>项目管理</template>
        </el-menu-item>
        
        <!-- 仪表盘 - 仅在选择项目后显示 -->
        <el-menu-item v-if="hasProject" index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <!-- 用例管理 - 仅在选择项目后显示 -->
        <el-menu-item v-if="hasProject" index="/test-cases">
          <el-icon><DocumentCopy /></el-icon>
          <template #title>用例管理</template>
        </el-menu-item>
        
        <!-- 执行记录 - 仅在选择项目后显示 -->
        <el-menu-item v-if="hasProject" :index="executionListPath">
          <el-icon><Tickets /></el-icon>
          <template #title>执行记录</template>
        </el-menu-item>
        
        <!-- 首页 - 仅在选择项目后显示 -->
        <el-menu-item v-if="hasProject" index="/home">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        
        <!-- 关于 - 始终显示 -->
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
          <el-divider direction="vertical" />
          <span class="current-project">
            <el-icon><Folder /></el-icon>
            {{ currentProjectName }}
          </span>
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
    
    .current-project {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      color: #606266;
      padding: 4px 12px;
      background-color: #f5f7fa;
      border-radius: 4px;
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
