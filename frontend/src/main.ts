import '@/styles/index.scss'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import ElementPlus, { ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import { useUserStore } from '@/stores/user'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue Error:', err)
  console.error('Component:', instance?.$options?.name || 'Anonymous')
  console.error('Error Info:', info)

  // 显示用户友好的错误提示
  ElMessage.error('应用发生错误，请刷新页面重试')

  // 生产环境可以上报到错误监控服务
  // if (import.meta.env.PROD) {
  //   reportError(err, { component: instance?.$options.name, info })
  // }
}

// 全局 Promise rejection 处理
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled Promise Rejection:', event.reason)

  // 生产环境可以上报到错误监控服务
  // if (import.meta.env.PROD) {
  //   reportError(event.reason)
  // }

  // 防止默认处理（避免在控制台显示两次错误）
  event.preventDefault()
})

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 应用启动时验证 Token 有效性
const userStore = useUserStore()
if (userStore.token) {
  // 尝试获取用户信息来验证 token
  userStore.fetchUserInfo().catch((error) => {
    console.warn('Token 验证失败，已清除登录状态:', error)
    // Token 无效，清除状态
    userStore.reset()
  })
}

app.mount('#app')
