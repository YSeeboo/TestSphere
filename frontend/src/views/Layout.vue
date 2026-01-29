<script setup lang="ts">
/**
 * 主布局组件
 * 包含头部导航、侧边栏和内容区域
 */
import { useProjectStore } from '@/stores/project'
import { useUserStore } from '@/stores/user'
import { DataAnalysis, DocumentCopy, Folder, HomeFilled, InfoFilled, Tickets, User } from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

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
    <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar glass-effect">
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
      <el-header class="header glass-effect">
        <div class="header-left">
          <el-button :icon="isCollapse ? 'Expand' : 'Fold'" @click="toggleSidebar" text />
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
  background-color: rgba(255, 255, 255, 0.8);
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  transition: width 0.3s;
  
  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 60px;
    background-color: transparent;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    
    h2 {
      margin: 0;
      color: #1d1d1f;
      font-size: 20px;
      font-weight: 600;
    }
  }
  
  .sidebar-menu {
    border-right: none;
    background-color: transparent;
    padding: 10px;

    :deep(.el-menu-item) {
      border-radius: 8px;
      margin-bottom: 4px;
      height: 44px;
      line-height: 44px;
      color: #1d1d1f;
      
      &:hover {
        background-color: rgba(0, 0, 0, 0.04);
      }

      &.is-active {
        background-color: #e5e5ea;
        color: #0071e3;
        font-weight: 500;
      }
    }
  }
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.8);
  border-bottom: none;
  padding: 0 20px;
  z-index: 10;
  
  .header-left {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 16px;
    
    .header-title {
      font-size: 18px;
      font-weight: 600;
      color: #1d1d1f;
    }
    
    .current-project {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      color: #1d1d1f;
      padding: 4px 12px;
      background-color: rgba(0, 0, 0, 0.04);
      border-radius: 6px;
    }
  }
  
  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 0 12px;
      height: 36px;
      border-radius: 18px;
      transition: background-color 0.3s;
      color: #1d1d1f;
      
      &:hover {
        background-color: rgba(0, 0, 0, 0.04);
      }
    }
  }
}

.main-content {
  background-color: var(--el-bg-color-page);
  padding: 24px;
}
</style>
