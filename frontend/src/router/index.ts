import { useUserStore } from '@/stores/user'
import { useProjectStore } from '@/stores/project'
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

/**
 * 路由元信息接口
 */
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean // 是否需要登录
    guest?: boolean // 是否是访客页面（登录后不可访问）
    requiresProject?: boolean // 是否需要选择项目
  }
}

const routes: RouteRecordRaw[] = [
  // 登录页面
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: '登录',
      guest: true, // 访客页面，已登录用户访问会跳转到首页
    },
  },
  // 注册页面
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: {
      title: '注册',
      guest: true, // 访客页面，已登录用户访问会跳转到首页
    },
  },
  // 主布局 (需要认证)
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    meta: {
      requiresAuth: true, // 需要登录才能访问
    },
    children: [
      // 仪表盘
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: {
          title: '仪表盘',
          requiresAuth: true,
          requiresProject: true, // 需要选择项目
        },
      },
      // 项目管理
      {
        path: '/projects',
        name: 'Projects',
        component: () => import('@/views/project/index.vue'),
        meta: {
          title: '项目管理',
          requiresAuth: true,
        },
      },
      // 用例管理
      {
        path: '/test-cases',
        name: 'TestCases',
        component: () => import('@/views/testCase/index.vue'),
        meta: {
          title: '用例管理',
          requiresAuth: true,
          requiresProject: true, // 需要选择项目
        },
      },
      // 执行记录列表
      {
        path: '/projects/:projectId/executions',
        name: 'ExecutionList',
        component: () => import('@/views/execution/list.vue'),
        meta: {
          title: '执行记录',
          requiresAuth: true,
          requiresProject: true, // 需要选择项目
        },
      },
      // 执行详情
      {
        path: '/executions/:id',
        name: 'ExecutionDetail',
        component: () => import('@/views/execution/detail.vue'),
        meta: {
          title: '执行详情',
          requiresAuth: true,
        },
      },
      // 定时任务设置
      {
        path: '/projects/:projectId/settings/cron',
        name: 'ProjectCronSettings',
        component: () => import('@/views/project/settings/index.vue'),
        meta: {
          title: '定时任务',
          requiresAuth: true,
          requiresProject: true,
        },
      },
      // 保留原有的首页路由（兼容性）
      {
        path: '/home',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: {
          title: '首页',
          requiresAuth: true,
          requiresProject: true, // 需要选择项目
        },
      },
      // 关于页面
      {
        path: '/about',
        name: 'About',
        component: () => import('@/views/About.vue'),
        meta: {
          title: '关于',
          requiresAuth: true,
        },
      },
    ],
  },
  // 404 页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '页面不存在',
    },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

/**
 * 全局前置守卫
 * 处理路由权限验证和页面标题设置
 */
router.beforeEach(async (to, _from, next) => {
  // 设置页面标题
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - ${import.meta.env.VITE_APP_TITLE || 'ATP'}`
  }

  // 获取用户 Store
  const userStore = useUserStore()
  const isLoggedIn = userStore.isLoggedIn

  // 需要认证的页面
  if (to.meta.requiresAuth) {
    if (!isLoggedIn) {
      // 未登录，跳转到登录页
      next({
        path: '/login',
        query: { redirect: to.fullPath }, // 保存原始目标路径，登录后可跳转回去
      })
      return
    }

    // 已有 token，但没有用户信息，需要验证 token 有效性
    if (!userStore.userInfo) {
      try {
        await userStore.fetchUserInfo()
      } catch (error) {
        // Token 无效，清除状态并跳转到登录页
        console.error('Token 验证失败，请重新登录')
        userStore.reset()
        next({
          path: '/login',
          query: { redirect: to.fullPath },
        })
        return
      }
    }

    // 需要选择项目的页面
    if (to.meta.requiresProject) {
      const projectStore = useProjectStore()
      
      // 如果没有选择项目，重定向到项目管理页
      if (!projectStore.currentProjectId) {
        next({
          path: '/projects',
          query: { redirect: to.fullPath }, // 保存原始目标路径
        })
        return
      }
    }
  }

  // 访客页面（登录、注册）
  if (to.meta.guest) {
    if (isLoggedIn) {
      // 已登录，跳转到首页
      next({ path: '/' })
      return
    }
  }

  // 放行
  next()
})

export default router
