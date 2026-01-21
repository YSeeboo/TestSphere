import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { useUserStore } from '@/stores/user'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 应用启动时验证 Token 有效性
const userStore = useUserStore()
if (userStore.token) {
  // 尝试获取用户信息来验证 token
  userStore.fetchUserInfo().catch(() => {
    // Token 无效，清除状态
    userStore.reset()
  })
}

app.mount('#app')
