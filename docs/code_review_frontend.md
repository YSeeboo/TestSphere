# 前端架构 Code Review 报告

## 审计范围
- 目录：`frontend/src`
- 关注点：Type Safety、状态管理 (Pinia)、错误处理

---

## 1. Type Safety 类型安全

### 1.1 ✅ 优点

#### 1.1.1 后端 Schema 一致性良好
前端类型定义与后端 Pydantic Schema 基本保持一致：

**Project 类型对比：**
```typescript
// frontend/src/types/project.ts
export interface Project {
  id: number
  name: string
  description: string | null
  owner_id: number
  git_url: string | null
  git_branch: string | null
  created_at: string
  updated_at: string
}
```

```python
# backend/app/schemas/project.py
class ProjectOut(ProjectInDB):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    git_url: Optional[str]
    git_branch: str
    last_sync_time: Optional[datetime]  # ⚠️ 前端缺失
    last_sync_status: str  # ⚠️ 前端缺失
    created_at: datetime
    updated_at: datetime
```

**TestCase 类型对比：**
```typescript
// frontend/src/types/testCase.ts ✅ 完全一致
export interface TestCase {
  id: number
  project_id: number
  file_path: string
  name: string
  description: string | null
  nodeid: string
  markers: Record<string, any> | null  // ⚠️ 使用了 any
  created_at: string
  updated_at: string
}
```

#### 1.1.2 API 函数有明确的返回类型
```typescript
// frontend/src/api/project.ts
export function getProjects(skip: number = 0, limit: number = 100): Promise<Project[]> {
  return request.get<Project[]>('/projects/', { params: { skip, limit } })
}

export function createProject(projectData: ProjectCreateForm): Promise<Project> {
  return request.post<Project>('/projects/', projectData)
}
```

### 1.2 ⚠️ 问题与改进建议

#### 问题 1: `any` 类型使用过多

**位置 1: `utils/request.ts` - 泛型默认值**
```typescript
// 当前实现
export const request = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, config)
  },
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config)
  },
}
```

**问题分析：**
- `T = any` 作为默认泛型会导致类型检查失效
- `data?: any` 参数缺乏类型约束
- 错误处理中使用 `(data as any)?.detail` 绕过类型检查

**建议改进：**
```typescript
// 定义通用响应类型
export interface ApiResponse<T = unknown> {
  data?: T
  message?: string
  code?: number
}

// 定义错误响应类型
export interface ApiErrorResponse {
  detail?: string
  message?: string
  errors?: Record<string, string[]>
}

// 改进后的 request 工具
export const request = {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, config)
  },
  
  post<T = unknown, D = unknown>(
    url: string, 
    data?: D, 
    config?: AxiosRequestConfig
  ): Promise<T> {
    return service.post(url, data, config)
  },
}

// 响应拦截器中的错误处理
(error: AxiosError<ApiErrorResponse>) => {
  if (error.response) {
    const { status, data } = error.response
    switch (status) {
      case 400:
        ElMessage.error(data?.detail || '请求参数错误')
        break
      // ...
    }
  }
}
```

**位置 2: `types/testCase.ts` - markers 字段**
```typescript
// 当前实现
export interface TestCase {
  markers: Record<string, any> | null  // ⚠️ any
}

// 建议改进
export interface PytestMarker {
  name: string
  args: unknown[]
  kwargs: Record<string, unknown>
}

export interface TestCase {
  markers: Record<string, PytestMarker> | null
}
```

**位置 3: `stores/user.ts` - 错误捕获**
```typescript
// 当前实现
} catch (error: any) {  // ⚠️ any
  const errorMessage = error.response?.data?.detail || error.message || '登录失败'
}

// 建议改进
import { AxiosError } from 'axios'
import type { ApiErrorResponse } from '@/types/api'

} catch (error) {
  const axiosError = error as AxiosError<ApiErrorResponse>
  const errorMessage = 
    axiosError.response?.data?.detail || 
    axiosError.message || 
    '登录失败'
}
```

#### 问题 2: 前端类型与后端 Schema 不完全一致

**Project 类型缺失字段：**
```typescript
// 后端有但前端缺失
export interface Project {
  // ... 现有字段
  last_sync_time?: string | null  // ⚠️ 缺失
  last_sync_status?: string        // ⚠️ 缺失
}
```

**建议：** 添加这些字段，即使前端暂时不使用，也能保证类型完整性。

#### 问题 3: 缺少 AxiosRequestConfig 类型导入

```typescript
// frontend/src/utils/request.ts
// ⚠️ 使用了 AxiosRequestConfig 但未导入
export const request = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    //                              ^^^^^^^^^^^^^^^^^^^ 未导入
  }
}
```

**建议：** 添加导入
```typescript
import type { AxiosRequestConfig } from 'axios'
```

#### 问题 4: 执行相关类型定义不一致

```typescript
// frontend/src/api/execution.ts
export interface RunTestResponse {
  id?: number            // ⚠️ 可选
  execution_id?: number  // ⚠️ 可选
  task_id?: string       // ⚠️ 可选
  status?: string        // ⚠️ 可选
  message?: string       // ⚠️ 可选
}
```

**问题分析：**
- 所有字段都是可选的，无法保证返回数据的结构
- 在使用时需要大量的空值检查

**建议改进：**
```typescript
// 根据后端实际返回定义精确类型
export interface RunTestResponse {
  execution_id: number  // 必填
  task_id: string       // 必填
  status: 'pending' | 'running'  // 使用字面量类型
  message?: string      // 可选
}
```

---

## 2. 状态管理 (Pinia)

### 2.1 ✅ 优点

#### 2.1.1 使用 Setup Syntax（推荐风格）
所有 Store 都使用了 Composition API 风格：

```typescript
// stores/user.ts
export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const userInfo = ref<UserInfo | null>(null)
  
  const isLoggedIn = computed(() => !!token.value)
  
  function setToken(newToken: string | null) { /* ... */ }
  
  return { token, userInfo, isLoggedIn, setToken }
})
```

**优点：**
- 符合 Vue 3 最佳实践
- 代码结构清晰，易于维护
- TypeScript 类型推断更好

#### 2.1.2 Store 职责划分清晰
- `useUserStore`: 用户认证和用户信息管理
- `useProjectStore`: 项目列表和当前项目管理
- `useCounterStore`: 示例 Store（可删除）

#### 2.1.3 持久化策略合理
```typescript
// stores/user.ts
const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))

function setToken(newToken: string | null) {
  token.value = newToken
  if (newToken) {
    localStorage.setItem(TOKEN_KEY, newToken)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}
```

### 2.2 ⚠️ 问题与改进建议

#### 问题 1: 存在循环依赖风险

**位置 1: `utils/request.ts` 中使用 `require()` 动态导入**
```typescript
// utils/request.ts - 请求拦截器
try {
  const { useUserStore } = require('@/stores/user')  // ⚠️ 动态导入
  const userStore = useUserStore()
  if (userStore.token && config.headers) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
} catch (error) {
  // 回退到 localStorage
  const token = localStorage.getItem('token')
}
```

**位置 2: `stores/user.ts` 中清理项目状态**
```typescript
// stores/user.ts - logout 方法
try {
  const { useProjectStore } = await import('@/stores/project')  // ⚠️ 动态导入
  const projectStore = useProjectStore()
  projectStore.reset()
} catch (error) {
  console.error('Failed to reset project store:', error)
}
```

**问题分析：**
- 使用 `require()` 和动态 `import()` 是为了避免循环依赖
- 这表明模块依赖关系设计不够清晰
- 动态导入会增加运行时开销和错误处理复杂度

**建议改进方案 1: 使用事件总线（推荐）**
```typescript
// utils/eventBus.ts
import mitt from 'mitt'

type Events = {
  'user:logout': void
  'user:login': { userId: number }
}

export const eventBus = mitt<Events>()

// stores/user.ts
import { eventBus } from '@/utils/eventBus'

async function logout(): Promise<void> {
  setToken(null)
  setUserInfo(null)
  
  // 发出登出事件
  eventBus.emit('user:logout')
  
  ElMessage.success('已退出登录')
  await router.push('/login')
}

// stores/project.ts
import { eventBus } from '@/utils/eventBus'

// 监听登出事件
eventBus.on('user:logout', () => {
  reset()
})
```

**建议改进方案 2: 直接从 localStorage 读取 token**
```typescript
// utils/request.ts - 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 直接从 localStorage 读取，避免依赖 Store
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  }
)
```

**优点：**
- 消除循环依赖
- 简化代码逻辑
- 减少运行时错误可能性

#### 问题 2: Store 初始化时机不明确

**位置: `stores/project.ts`**
```typescript
export const useProjectStore = defineStore('project', () => {
  const currentProjectId = ref<number | null>(null)
  
  // ⚠️ init() 方法需要手动调用
  function init() {
    const saved = localStorage.getItem(ACTIVE_PROJECT_KEY)
    if (saved) {
      const id = parseInt(saved, 10)
      if (!isNaN(id)) {
        currentProjectId.value = id
      }
    }
  }
  
  return { init, /* ... */ }
})
```

**问题分析：**
- `init()` 方法需要在应用启动时手动调用
- 如果忘记调用，会导致状态丢失
- 没有找到调用 `init()` 的地方

**建议改进：**
```typescript
export const useProjectStore = defineStore('project', () => {
  // 直接在定义时初始化
  const currentProjectId = ref<number | null>(() => {
    const saved = localStorage.getItem(ACTIVE_PROJECT_KEY)
    if (saved) {
      const id = parseInt(saved, 10)
      return isNaN(id) ? null : id
    }
    return null
  })
  
  // 移除 init() 方法，不需要了
  return { currentProjectId, /* ... */ }
})
```

#### 问题 3: 缺少 Store 状态重置的统一机制

**当前实现：**
```typescript
// stores/user.ts
function reset() {
  setToken(null)
  setUserInfo(null)
  
  // ⚠️ 手动清理其他 Store
  try {
    const { useProjectStore } = require('@/stores/project')
    const projectStore = useProjectStore()
    projectStore.reset()
  } catch (error) {
    console.debug('Project store not initialized yet')
  }
}
```

**建议改进：使用 Pinia 插件**
```typescript
// stores/index.ts
import { createPinia } from 'pinia'

export const pinia = createPinia()

// 添加重置插件
pinia.use(({ store }) => {
  const initialState = JSON.parse(JSON.stringify(store.$state))
  
  store.$reset = () => {
    store.$patch(initialState)
  }
})

// stores/user.ts
function logout(): Promise<void> {
  // 重置所有 Store
  const pinia = getActivePinia()
  if (pinia) {
    pinia._s.forEach(store => {
      if (store.$reset) {
        store.$reset()
      }
    })
  }
  
  await router.push('/login')
}
```

#### 问题 4: 缺少 Store 的错误边界处理

**当前实现：**
```typescript
// stores/project.ts
async function loadProjects(): Promise<void> {
  try {
    const projectList = await getProjects()
    projects.value = projectList
  } catch (error) {
    console.error('Failed to load projects:', error)
    ElMessage.error('获取项目列表失败')  // ⚠️ 直接在 Store 中显示 UI 提示
    throw error  // ⚠️ 抛出错误但没有统一处理
  }
}
```

**问题分析：**
- Store 中混合了业务逻辑和 UI 逻辑（ElMessage）
- 错误处理不统一，有些地方 throw，有些地方不 throw
- 调用方无法区分错误类型

**建议改进：**
```typescript
// types/error.ts
export class ApiError extends Error {
  constructor(
    message: string,
    public code?: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// stores/project.ts
async function loadProjects(): Promise<void> {
  try {
    const projectList = await getProjects()
    projects.value = projectList
  } catch (error) {
    console.error('Failed to load projects:', error)
    // 不在 Store 中显示 UI 提示，由调用方决定
    throw new ApiError(
      '获取项目列表失败',
      'LOAD_PROJECTS_FAILED',
      (error as AxiosError).response?.status,
      error
    )
  }
}

// views/project/index.vue
async function loadProjectList() {
  loading.value = true
  try {
    await projectStore.loadProjects()
  } catch (error) {
    if (error instanceof ApiError) {
      ElMessage.error(error.message)
      // 可以根据 error.code 做不同处理
    }
  } finally {
    loading.value = false
  }
}
```

---

## 3. 错误处理

### 3.1 ✅ 优点

#### 3.1.1 请求拦截器覆盖了主要 HTTP 错误

```typescript
// utils/request.ts - 响应拦截器
(error: AxiosError) => {
  if (error.response) {
    const { status, data } = error.response
    switch (status) {
      case 400: ElMessage.error((data as any)?.detail || '请求参数错误'); break
      case 401: /* 处理未授权，跳转登录 */; break
      case 403: ElMessage.error('拒绝访问'); break
      case 404: ElMessage.error('请求的资源不存在'); break
      case 500: ElMessage.error('服务器内部错误'); break
      case 503: ElMessage.error('服务暂时不可用'); break
      default: ElMessage.error((data as any)?.detail || `请求失败 (${status})`);
    }
  } else if (error.request) {
    ElMessage.error('网络错误，请检查您的网络连接')  // ✅ 处理网络断开
  } else {
    ElMessage.error(error.message || '请求失败')
  }
  return Promise.reject(error)
}
```

**优点：**
- 覆盖了网络断开、超时等异常
- 401 错误会自动清除 token 并跳转登录
- 用户体验友好

#### 3.1.2 组件中的错误处理较为完善

```typescript
// views/testCase/index.vue
async function loadTestCases() {
  loading.value = true
  try {
    const response = await getTestCases(projectId, { limit, offset })
    testCases.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('加载测试用例失败:', error)
    ElMessage.error('加载测试用例失败')
  } finally {
    loading.value = false  // ✅ 确保 loading 状态被重置
  }
}
```

### 3.2 ⚠️ 问题与改进建议

#### 问题 1: 缺少超时配置和重试机制

**当前实现：**
```typescript
// utils/request.ts
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API || '/api/v1',
  timeout: 15000,  // ⚠️ 固定 15 秒超时
})
```

**问题分析：**
- 所有请求使用相同的超时时间
- 没有重试机制
- 长时间运行的任务（如同步、执行测试）可能超时

**建议改进：**
```typescript
// utils/request.ts
import axios, { AxiosRequestConfig } from 'axios'
import axiosRetry from 'axios-retry'

const service = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API || '/api/v1',
  timeout: 15000,
})

// 配置重试
axiosRetry(service, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    // 只对网络错误和 5xx 错误重试
    return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
           (error.response?.status ?? 0) >= 500
  },
})

// 支持自定义超时
export const request = {
  get<T = unknown>(
    url: string, 
    config?: AxiosRequestConfig & { timeout?: number }
  ): Promise<T> {
    return service.get(url, config)
  },
}

// 使用示例
// 长时间任务使用更长的超时
await request.post('/projects/1/sync', {}, { timeout: 60000 })
```

#### 问题 2: 401 错误处理可能导致死循环

**当前实现：**
```typescript
// utils/request.ts - 响应拦截器
case 401:
  ElMessage.error('登录已过期，请重新登录')
  
  try {
    const { useUserStore } = require('@/stores/user')
    const userStore = useUserStore()
    userStore.reset()
    
    // ⚠️ 强制跳转
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  } catch (e) {
    localStorage.removeItem('token')
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }
  break
```

**问题分析：**
- 如果在登录页面调用 API 返回 401，会陷入死循环
- 使用 `window.location.href` 会导致页面刷新，丢失状态
- 多个 401 错误会显示多个错误提示

**建议改进：**
```typescript
// utils/request.ts
let isRefreshing = false
let failedQueue: Array<{ resolve: Function; reject: Function }> = []

const processQueue = (error: Error | null) => {
  failedQueue.forEach(promise => {
    if (error) {
      promise.reject(error)
    } else {
      promise.resolve()
    }
  })
  failedQueue = []
}

service.interceptors.response.use(
  (response) => response.data,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }
    
    if (error.response?.status === 401) {
      // 避免在登录页面重复跳转
      if (window.location.pathname === '/login') {
        return Promise.reject(error)
      }
      
      // 防止多次刷新 token
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => {
          return service(originalRequest)
        })
      }
      
      // 只显示一次错误提示
      if (!originalRequest._retry) {
        ElMessage.error('登录已过期，请重新登录')
        originalRequest._retry = true
      }
      
      isRefreshing = true
      
      // 清除状态并跳转
      const { useUserStore } = await import('@/stores/user')
      const userStore = useUserStore()
      userStore.reset()
      
      // 使用 router 而不是 window.location
      const router = await import('@/router')
      router.default.push('/login')
      
      isRefreshing = false
      processQueue(new Error('Token expired'))
      
      return Promise.reject(error)
    }
    
    // 其他错误处理...
    return Promise.reject(error)
  }
)
```

#### 问题 3: 组件中存在未捕获的 Promise rejection

**位置 1: `views/testCase/index.vue`**
```typescript
// ⚠️ ElMessageBox.confirm 的 rejection 未完全处理
async function handleSync() {
  try {
    await ElMessageBox.confirm('...', '确认同步', { /* ... */ })
    syncing.value = true
    await projectStore.syncProject(projectId)
    // ...
  } catch (error) {
    if (error !== 'cancel') {  // ⚠️ 字符串比较不可靠
      console.error('同步失败:', error)
      ElMessage.error('同步失败')
      syncing.value = false
    }
  }
}
```

**问题分析：**
- `ElMessageBox.confirm` 取消时会 reject，值为 `'cancel'`
- 使用字符串比较不够健壮
- `syncing.value = false` 只在非取消错误时执行，可能导致状态不一致

**建议改进：**
```typescript
async function handleSync() {
  const projectId = projectStore.currentProjectId
  if (!projectId) {
    ElMessage.warning('请先选择项目')
    return
  }

  try {
    await ElMessageBox.confirm(
      '同步将从 Git 仓库拉取最新代码并收集测试用例，可能需要一些时间。是否继续？',
      '确认同步',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
  } catch (error) {
    // 用户取消，直接返回
    return
  }

  syncing.value = true
  try {
    await projectStore.syncProject(projectId)
    ElMessage.success('同步任务已提交，3秒后将自动刷新列表')

    setTimeout(() => {
      loadTestCases()
      syncing.value = false
    }, 3000)
  } catch (error) {
    console.error('同步失败:', error)
    ElMessage.error('同步失败')
    syncing.value = false
  }
}
```

**位置 2: `main.ts` - 应用启动时的 token 验证**
```typescript
// main.ts
const userStore = useUserStore()
if (userStore.token) {
  // ⚠️ catch 中没有任何处理
  userStore.fetchUserInfo().catch(() => {
    userStore.reset()
  })
}
```

**建议改进：**
```typescript
// main.ts
const userStore = useUserStore()
if (userStore.token) {
  userStore.fetchUserInfo().catch((error) => {
    console.warn('Token 验证失败，已清除登录状态:', error)
    userStore.reset()
  })
}
```

#### 问题 4: 缺少全局错误处理

**当前状态：**
- 没有全局的 Vue 错误处理器
- 没有全局的 Promise rejection 处理器

**建议添加：**
```typescript
// main.ts
import { createApp } from 'vue'

const app = createApp(App)

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue Error:', err)
  console.error('Error Info:', info)
  
  // 可以上报到错误监控服务
  // reportError(err, { component: instance?.$options.name, info })
  
  ElMessage.error('应用发生错误，请刷新页面重试')
}

// 全局 Promise rejection 处理
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled Promise Rejection:', event.reason)
  
  // 可以上报到错误监控服务
  // reportError(event.reason)
  
  event.preventDefault()
})

app.mount('#app')
```

#### 问题 5: 轮询机制缺少错误处理

**位置: `views/execution/detail.vue`**
```typescript
function startPolling() {
  if (pollingTimer !== null) return
  pollingTimer = window.setInterval(() => {
    loadExecutionDetail()  // ⚠️ 如果失败会怎样？
  }, 2000)
}

async function loadExecutionDetail() {
  loading.value = true
  try {
    const detail = await getExecutionDetail(executionId.value)
    execution.value = detail
    
    if (shouldPoll(detail.status)) {
      startPolling()
    } else if (isTerminal(detail.status)) {
      stopPolling()
    }
  } catch (error) {
    console.error('加载执行详情失败:', error)
    ElMessage.error('加载执行详情失败')  // ⚠️ 每 2 秒显示一次错误？
  } finally {
    loading.value = false
  }
}
```

**问题分析：**
- 轮询过程中如果 API 失败，会每 2 秒显示一次错误提示
- 没有重试次数限制
- 没有指数退避策略

**建议改进：**
```typescript
let pollingTimer: number | null = null
let pollingErrorCount = 0
const MAX_POLLING_ERRORS = 3

async function loadExecutionDetail(silent = false) {
  if (!silent) {
    loading.value = true
  }
  
  try {
    const detail = await getExecutionDetail(executionId.value)
    execution.value = detail
    
    // 重置错误计数
    pollingErrorCount = 0
    
    if (shouldPoll(detail.status)) {
      startPolling()
    } else if (isTerminal(detail.status)) {
      stopPolling()
    }
  } catch (error) {
    console.error('加载执行详情失败:', error)
    
    pollingErrorCount++
    
    // 只在非轮询模式或错误次数超过阈值时显示提示
    if (!silent || pollingErrorCount >= MAX_POLLING_ERRORS) {
      ElMessage.error('加载执行详情失败')
      stopPolling()  // 停止轮询
    }
  } finally {
    if (!silent) {
      loading.value = false
    }
  }
}

function startPolling() {
  if (pollingTimer !== null) return
  pollingTimer = window.setInterval(() => {
    loadExecutionDetail(true)  // 静默模式，不显示 loading
  }, 2000)
}
```

---

## 4. 其他问题

### 4.1 路由守卫中的异步操作未完全处理

**位置: `router/index.ts`**
```typescript
router.beforeEach(async (to, _from, next) => {
  // ...
  
  if (!userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()  // ⚠️ 如果失败会怎样？
    } catch (error) {
      console.error('Token 验证失败，请重新登录')
      userStore.reset()
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
  }
  
  // ...
})
```

**建议改进：** 添加 loading 状态，避免闪烁
```typescript
// App.vue
<template>
  <div v-if="appReady">
    <router-view />
  </div>
  <div v-else class="app-loading">
    <el-icon class="is-loading"><Loading /></el-icon>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const appReady = ref(false)
const userStore = useUserStore()

onMounted(async () => {
  if (userStore.token) {
    try {
      await userStore.fetchUserInfo()
    } catch (error) {
      userStore.reset()
    }
  }
  appReady.value = true
})
</script>
```

### 4.2 缺少请求取消机制

**问题场景：**
- 用户快速切换页面时，前一个页面的请求可能还在进行
- 组件卸载时，pending 的请求没有被取消

**建议改进：**
```typescript
// composables/useRequest.ts
import { ref, onUnmounted } from 'vue'
import axios, { CancelTokenSource } from 'axios'

export function useRequest<T>() {
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const data = ref<T | null>(null)
  
  let cancelTokenSource: CancelTokenSource | null = null
  
  async function execute(requestFn: () => Promise<T>) {
    // 取消之前的请求
    if (cancelTokenSource) {
      cancelTokenSource.cancel('New request initiated')
    }
    
    cancelTokenSource = axios.CancelToken.source()
    loading.value = true
    error.value = null
    
    try {
      data.value = await requestFn()
    } catch (err) {
      if (!axios.isCancel(err)) {
        error.value = err as Error
      }
    } finally {
      loading.value = false
    }
  }
  
  // 组件卸载时取消请求
  onUnmounted(() => {
    if (cancelTokenSource) {
      cancelTokenSource.cancel('Component unmounted')
    }
  })
  
  return { loading, error, data, execute }
}

// 使用示例
const { loading, data, execute } = useRequest<TestCase[]>()

onMounted(() => {
  execute(() => getTestCases(projectId, { limit: 20, offset: 0 }))
})
```

### 4.3 缺少开发环境的 API Mock

**建议添加：**
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import { viteMockServe } from 'vite-plugin-mock'

export default defineConfig({
  plugins: [
    viteMockServe({
      mockPath: 'mock',
      enable: process.env.NODE_ENV === 'development',
    }),
  ],
})

// mock/project.ts
import { MockMethod } from 'vite-plugin-mock'

export default [
  {
    url: '/api/v1/projects',
    method: 'get',
    response: () => {
      return [
        { id: 1, name: 'Test Project', description: 'Mock data' },
      ]
    },
  },
] as MockMethod[]
```

---

## 5. 总结与优先级建议

### 5.1 高优先级（必须修复）

1. **修复 `utils/request.ts` 中缺失的 `AxiosRequestConfig` 导入**
   - 影响：TypeScript 编译错误
   - 工作量：5 分钟

2. **消除循环依赖风险**
   - 影响：代码可维护性、运行时稳定性
   - 工作量：2 小时
   - 方案：使用事件总线或直接读取 localStorage

3. **修复 401 错误处理的死循环风险**
   - 影响：用户体验、应用稳定性
   - 工作量：1 小时

4. **添加全局错误处理**
   - 影响：错误监控、用户体验
   - 工作量：1 小时

### 5.2 中优先级（建议修复）

1. **减少 `any` 类型使用**
   - 影响：类型安全、代码质量
   - 工作量：4 小时

2. **完善前端类型与后端 Schema 的一致性**
   - 影响：类型安全、API 调用正确性
   - 工作量：2 小时

3. **改进 Store 初始化机制**
   - 影响：代码健壮性
   - 工作量：1 小时

4. **优化轮询机制的错误处理**
   - 影响：用户体验
   - 工作量：1 小时

### 5.3 低优先级（可选优化）

1. **添加请求重试机制**
   - 影响：网络容错性
   - 工作量：2 小时

2. **实现请求取消机制**
   - 影响：性能优化
   - 工作量：3 小时

3. **添加 API Mock 支持**
   - 影响：开发效率
   - 工作量：4 小时

4. **删除 `useCounterStore` 示例代码**
   - 影响：代码整洁
   - 工作量：5 分钟

---

## 6. 代码规范性评分

| 维度 | 评分 | 说明 |
|------|------|------|
| **Type Safety** | 7/10 | 基本类型定义完善，但存在 `any` 滥用问题 |
| **状态管理** | 8/10 | 使用 Setup Syntax，职责清晰，但存在循环依赖风险 |
| **错误处理** | 7/10 | 覆盖主要场景，但缺少全局处理和边界情况处理 |
| **代码组织** | 9/10 | 目录结构清晰，符合 Vue 3 最佳实践 |
| **可维护性** | 7/10 | 整体良好，但动态导入和循环依赖降低了可维护性 |

**总体评分：7.6/10**

---

## 7. 推荐阅读

- [Vue 3 TypeScript 最佳实践](https://vuejs.org/guide/typescript/overview.html)
- [Pinia 官方文档](https://pinia.vuejs.org/)
- [Axios 拦截器最佳实践](https://axios-http.com/docs/interceptors)
- [前端错误监控方案](https://sentry.io/for/vue/)
