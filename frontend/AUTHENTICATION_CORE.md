# 前端认证核心逻辑实现文档

## 概述

本文档描述了前端认证系统的核心逻辑层实现，包括路由守卫、用户状态管理和网络请求拦截。

## 实现的文件

### 1. 类型定义文件

#### `frontend/src/types/user.ts`
定义了用户相关的 TypeScript 接口：
- `UserInfo`: 用户信息接口
- `UserRegisterForm`: 用户注册表单
- `UserLoginForm`: 用户登录表单
- `UserUpdateForm`: 用户更新表单

#### `frontend/src/types/auth.ts`
定义了认证相关的 TypeScript 接口：
- `TokenResponse`: Token 响应接口
- `TokenPayload`: Token Payload 接口

### 2. API 调用层

#### `frontend/src/api/auth.ts`
实现了认证相关的 API 调用函数：
- `login(loginForm)`: 用户登录 API，调用 `/auth/login-json`
- `register(registerForm)`: 用户注册 API，调用 `/auth/register`
- `getMe()`: 获取当前用户信息 API，调用 `/users/me`
- `updateMe(updateData)`: 更新当前用户信息 API，调用 `/users/me`

### 3. 状态管理层

#### `frontend/src/stores/user.ts`
使用 Pinia Setup Syntax 实现的用户状态管理：

**State:**
- `token`: Token 字符串（从 localStorage 初始化）
- `userInfo`: 用户信息对象

**Computed:**
- `isLoggedIn`: 是否已登录
- `isSuperUser`: 是否是超级管理员

**Actions:**
- `setToken(newToken)`: 设置 Token 并同步到 localStorage
- `setUserInfo(info)`: 设置用户信息
- `fetchUserInfo()`: 获取当前用户信息
- `login(loginForm)`: 用户登录逻辑
  - 调用登录 API
  - 保存 Token
  - 获取用户信息
  - 跳转到首页
- `logout()`: 用户登出逻辑
  - 清除 Token
  - 清除用户信息
  - 跳转到登录页
- `reset()`: 重置 Store 状态

### 4. 网络请求拦截

#### `frontend/src/utils/request.ts`
修改了 Axios 请求封装，添加了认证相关的拦截器：

**请求拦截器:**
- 从 Pinia Store 获取 Token
- 自动添加 `Authorization: Bearer <token>` 到请求头
- 避免循环依赖：在拦截器内部动态导入 Store

**响应拦截器:**
- 监听 401 未授权错误
- 自动调用 `userStore.reset()` 清除认证状态
- 使用 `window.location.href` 强制跳转到登录页（避免路由守卫的影响）

### 5. 路由配置与守卫

#### `frontend/src/router/index.ts`
重构了路由配置，实现了完整的认证路由守卫：

**路由结构:**
- `/login`: 登录页（meta: { guest: true }）
- `/register`: 注册页（meta: { guest: true }）
- `/`: Layout 主布局（meta: { requiresAuth: true }）
  - `/dashboard`: 仪表盘（meta: { requiresAuth: true }）
  - `/home`: 首页（meta: { requiresAuth: true }）
  - `/about`: 关于页面（meta: { requiresAuth: true }）
- `/:pathMatch(.*)*`: 404 页面

**全局前置守卫 (beforeEach):**
1. **设置页面标题**: 根据 route.meta.title 动态设置
2. **认证检查**: 
   - 若目标路由需要 `requiresAuth` 且用户未登录 → 跳转到 `/login`
   - 保存原始目标路径到 query.redirect，登录后可跳转回去
3. **访客页面检查**:
   - 若目标路由是 `guest` 页面且用户已登录 → 跳转到 `/`

**路由元信息扩展:**
```typescript
interface RouteMeta {
  title?: string        // 页面标题
  requiresAuth?: boolean // 是否需要登录
  guest?: boolean       // 是否是访客页面（登录后不可访问）
}
```

### 6. 视图组件（基础实现）

#### `frontend/src/views/Login.vue`
登录页面基础实现：
- 登录表单（邮箱、密码）
- 调用 `userStore.login()` 处理登录
- 提供跳转到注册页的链接

#### `frontend/src/views/Register.vue`
注册页面基础实现：
- 注册表单（邮箱、用户名、密码）
- 调用 `register()` API
- 注册成功后跳转到登录页

#### `frontend/src/views/Layout.vue`
主布局组件：
- 侧边栏导航（可折叠）
- 顶部导航栏（用户信息、退出登录）
- 内容区域（router-view）

#### `frontend/src/views/Dashboard.vue`
仪表盘页面：
- 显示测试统计数据（总数、运行中、通过、失败）
- 欢迎信息

#### `frontend/src/views/NotFound.vue`
404 页面：
- 错误提示
- 返回首页/上一页按钮

## 关键技术点

### 1. 避免循环依赖
在 `request.ts` 中，使用 `require()` 在拦截器内部动态导入 Store，避免模块循环依赖：

```typescript
try {
  const { useUserStore } = require('@/stores/user')
  const userStore = useUserStore()
  // 使用 userStore...
} catch (error) {
  // 回退方案
}
```

### 2. Token 持久化
Token 存储在 localStorage 中，刷新页面后自动恢复登录状态：

```typescript
const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
```

### 3. 401 错误处理
使用 `window.location.href` 强制刷新跳转，确保清除所有状态：

```typescript
if (window.location.pathname !== '/login') {
  window.location.href = '/login'
}
```

### 4. 路由守卫保护
结合 `requiresAuth` 和 `guest` 两种元信息，实现完整的路由权限控制：

- `requiresAuth`: 需要登录才能访问（Dashboard、Home 等）
- `guest`: 只有未登录用户才能访问（Login、Register）

### 5. 类型安全
所有 API 调用、Store State 和表单数据都有完整的 TypeScript 类型定义，确保类型安全。

## 工作流程

### 登录流程
1. 用户在 Login 页面输入邮箱和密码
2. 调用 `userStore.login(loginForm)`
3. Store 调用 `login()` API，获取 Token
4. Store 保存 Token 到 localStorage
5. Store 调用 `getMe()` API，获取用户信息
6. 跳转到首页（或 query.redirect 指定的页面）

### 路由守卫流程
1. 用户访问某个路由
2. `beforeEach` 守卫检查路由元信息
3. 如果需要认证且未登录 → 跳转到 `/login`
4. 如果是访客页面且已登录 → 跳转到 `/`
5. 否则放行

### 请求拦截流程
1. 前端发起 API 请求
2. 请求拦截器自动添加 `Authorization` 头
3. 后端验证 Token
4. 如果返回 401 → 响应拦截器清除状态并跳转到登录页
5. 否则返回数据

### 登出流程
1. 用户点击退出登录
2. 调用 `userStore.logout()`
3. 清除 Token 和用户信息
4. 跳转到 `/login`

## 后续工作

本实现完成了核心逻辑层，后续需要：

1. **Part 2 - UI 完善**:
   - 完善登录/注册页面的表单验证
   - 添加表单验证规则（邮箱格式、密码长度等）
   - 优化 UI/UX（Loading 状态、错误提示等）

2. **Part 3 - 功能增强**:
   - Token 自动刷新机制
   - 记住登录状态（记住我功能）
   - 密码找回功能
   - 用户个人中心页面

3. **测试**:
   - 单元测试（Store Actions、API 调用）
   - 集成测试（路由守卫、拦截器）
   - E2E 测试（登录流程）

## 注意事项

1. **安全性**:
   - Token 存储在 localStorage 中，存在 XSS 风险
   - 建议生产环境使用 HttpOnly Cookie 或更安全的存储方案

2. **错误处理**:
   - 所有 API 调用都有 try-catch 错误处理
   - 用户友好的错误提示信息

3. **用户体验**:
   - 登录成功后自动跳转到原始目标页面（redirect）
   - 401 错误时显示友好提示
   - Loading 状态显示

## 相关文件清单

- `frontend/src/types/user.ts` ✓
- `frontend/src/types/auth.ts` ✓
- `frontend/src/api/auth.ts` ✓
- `frontend/src/stores/user.ts` ✓
- `frontend/src/utils/request.ts` ✓ (修改)
- `frontend/src/router/index.ts` ✓ (重构)
- `frontend/src/views/Login.vue` ✓
- `frontend/src/views/Register.vue` ✓
- `frontend/src/views/Layout.vue` ✓
- `frontend/src/views/Dashboard.vue` ✓
- `frontend/src/views/NotFound.vue` ✓

所有文件均已实现并通过 Linter 检查。
