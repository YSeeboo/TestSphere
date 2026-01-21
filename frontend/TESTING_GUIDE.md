# 前端认证功能测试指南

## 已完成的功能

### 1. 登录页面 (`/login`)
- ✅ 居中 Card 布局，渐变色背景
- ✅ Email 字段：必填，email 格式验证
- ✅ Password 字段：必填，type=password，最少6位
- ✅ 登录按钮：带 loading 状态
- ✅ 注册链接：跳转到注册页
- ✅ 支持回车键提交表单

### 2. 注册页面 (`/register`)
- ✅ 居中 Card 布局，渐变色背景
- ✅ Email 字段：必填，email 格式验证
- ✅ Username 字段：必填，3-20 个字符
- ✅ Password 字段：必填，最少6位
- ✅ Confirm Password 字段：必填，必须与密码一致
- ✅ 前端校验：两次密码一致性验证
- ✅ 注册按钮：带 loading 状态
- ✅ 登录链接：跳转回登录页
- ✅ 支持回车键提交表单

### 3. Layout 布局 (`/`)
- ✅ 使用 `el-container` 结构
- ✅ `el-aside`：侧边栏，显示 "ATP Platform" logo 和菜单
- ✅ `el-header`：顶部导航，显示 "ATP Platform" 和用户信息
- ✅ 退出登录按钮：点击后跳转到登录页
- ✅ `el-main`：内容区，使用 `<router-view />`

### 4. Dashboard 页面 (`/dashboard`)
- ✅ 简单的欢迎页面
- ✅ 显示 "Welcome, {{ user.email }}"
- ✅ 显示用户详细信息（邮箱、用户名、账户类型）

## 测试步骤

### 前置条件
确保后端服务正在运行（端口 8000）。如果没有运行，请先启动：

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

### 启动前端开发服务器

```bash
cd frontend
npm run dev
```

访问 http://localhost:5173

### 测试用例

#### 测试 1: 注册新用户
1. 访问 http://localhost:5173，应该自动跳转到 `/login`
2. 点击"注册账号"按钮
3. 填写表单：
   - 邮箱: `test@example.com`
   - 用户名: `testuser`
   - 密码: `123456`
   - 确认密码: `123456`
4. 点击"注册"按钮
5. ✅ 应该显示"注册成功，请登录"提示
6. ✅ 自动跳转到登录页

#### 测试 2: 表单验证
1. 在注册页面，尝试提交空表单
2. ✅ 应该显示"请输入邮箱"、"请输入用户名"等错误提示
3. 输入错误格式的邮箱（如 `test`）
4. ✅ 应该显示"请输入正确的邮箱格式"
5. 两次密码输入不一致
6. ✅ 应该显示"两次输入的密码不一致"

#### 测试 3: 用户登录
1. 在登录页面填写：
   - 邮箱: `test@example.com`
   - 密码: `123456`
2. 点击"登录"按钮
3. ✅ 应该显示"登录成功"提示
4. ✅ 自动跳转到 Dashboard (`/dashboard`)
5. ✅ Dashboard 显示 "欢迎, test@example.com"

#### 测试 4: 登录态持久化
1. 登录成功后，刷新页面（F5 或 Cmd+R）
2. ✅ 应该保持登录状态，不跳转到登录页
3. ✅ 用户信息依然显示正确

#### 测试 5: 退出登录
1. 在任何需要认证的页面（Dashboard/Home/About）
2. 点击右上角用户名下拉菜单
3. 点击"退出登录"
4. ✅ 应该显示"已退出登录"提示
5. ✅ 自动跳转到登录页
6. ✅ localStorage 中的 token 已清除

#### 测试 6: 路由守卫
1. 未登录状态下，直接访问 http://localhost:5173/dashboard
2. ✅ 应该自动跳转到登录页
3. 登录后，访问 http://localhost:5173/login
4. ✅ 应该自动跳转到 Dashboard

## 验收标准

- ✅ 登录成功后自动跳转 Dashboard
- ✅ 刷新页面后登录态不丢失（Token 在 localStorage）
- ✅ 点击退出登录能回到登录页
- ✅ 所有表单验证正常工作
- ✅ UI 美观，使用 Element Plus 组件

## 技术实现要点

1. **表单验证**: 使用 Element Plus 的 `el-form` + `rules` 进行验证
2. **登录态管理**: 使用 Pinia Store + localStorage
3. **路由守卫**: 在 `router/index.ts` 中实现 `beforeEach` 守卫
4. **自动跳转**: 登录/注册/退出后使用 `router.push()` 或 `router.replace()`
5. **Token 持久化**: 在 `stores/user.ts` 中实现，登录时保存到 localStorage，页面刷新时从 localStorage 恢复

## 注意事项

- 图标库 `@element-plus/icons-vue` 已安装并在 `main.ts` 中全局注册
- 所有页面使用 Vue 3 Composition API (`<script setup>`)
- 类型定义使用 TypeScript 接口
- 样式使用 SCSS（scoped）
