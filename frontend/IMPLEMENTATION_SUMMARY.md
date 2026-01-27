# 项目管理 Part 2.1 - 前端逻辑层实现总结

## 完成时间
2026-01-26

## 实现文件

### 1. `frontend/src/types/project.ts`
定义了项目相关的 TypeScript 类型接口:

- **`Project`**: 项目完整信息接口
  - `id: number` - 项目 ID
  - `name: string` - 项目名称
  - `description: string | null` - 项目描述
  - `owner_id: number` - 所有者 ID
  - `created_at: string` - 创建时间
  - `updated_at: string` - 更新时间

- **`ProjectCreate`**: 项目创建数据接口
  - `name: string` - 项目名称 (必填)
  - `description?: string` - 项目描述 (可选)

- **`ProjectCreateForm`**: `ProjectCreate` 的类型别名，保持向后兼容

- **`ProjectUpdateForm`**: 项目更新数据接口
  - `name?: string` - 项目名称 (可选)
  - `description?: string` - 项目描述 (可选)

### 2. `frontend/src/api/project.ts`
封装了项目相关的 API 调用函数:

- **`getProjects(skip?, limit?)`**: 获取项目列表
  - 参数: `skip` (跳过记录数), `limit` (返回记录数上限)
  - 返回: `Promise<Project[]>`

- **`createProject(projectData)`**: 创建新项目
  - 参数: `ProjectCreateForm` 类型的项目数据
  - 返回: `Promise<Project>`

- **`getProject(projectId)`**: 获取单个项目详情
  - 参数: `projectId` (项目 ID)
  - 返回: `Promise<Project>`

- **`updateProject(projectId, projectData)`**: 更新项目信息
  - 参数: `projectId`, `ProjectUpdateForm` 类型的更新数据
  - 返回: `Promise<Project>`

- **`deleteProject(projectId)`**: 删除项目
  - 参数: `projectId` (项目 ID)
  - 返回: `Promise<void>`

### 3. `frontend/src/stores/project.ts`
使用 Pinia Setup Syntax 实现的项目状态管理:

#### State (状态)
- **`projects`**: `Project[]` - 项目列表
- **`currentProjectId`**: `number | null` - 当前选中的项目 ID

#### Getters (计算属性)
- **`currentProject`**: 根据 `currentProjectId` 返回对应的 `Project` 对象

#### Actions (操作方法)
- **`init()`**: 从 `localStorage` 读取 `active_project_id` 恢复状态
- **`selectProject(id)`**: 设置 `currentProjectId` 并存入 `localStorage` (key: "active_project_id")
- **`loadProjects()`**: 调用 API 获取项目列表并存入 state
  - 自动检查当前选中的项目是否在列表中，不存在则清除
- **`create(data)`**: 调用 API 创建项目，然后重新 `loadProjects()`
- **`deleteProject(projectId)`**: 调用 API 删除项目，更新本地列表
  - 如果删除的是当前项目，自动清除 `currentProjectId`

## 技术特性

### 类型安全
✅ 所有 API 调用都有完整的 Request/Response 类型定义
✅ 使用 TypeScript 泛型确保类型推导准确
✅ Pinia Store 使用 Setup Syntax，类型推导更强

### 状态持久化
✅ 使用 `localStorage` 存储当前选中的项目 ID (key: `active_project_id`)
✅ 提供 `init()` 方法在应用启动时恢复状态

### 错误处理
✅ 所有异步操作都有 try-catch 错误处理
✅ 使用 Element Plus 的 `ElMessage` 显示用户友好的错误提示
✅ 错误会被重新抛出，方便上层组件处理

### 数据一致性
✅ 创建项目后自动重新加载列表，确保数据最新
✅ 删除项目后自动从列表移除，避免额外请求
✅ 自动检查当前选中项目的有效性

## 使用示例

```typescript
import { useProjectStore } from '@/stores/project'

// 在组件中使用
const projectStore = useProjectStore()

// 初始化 (通常在 App.vue 或 Layout 中调用)
projectStore.init()

// 加载项目列表
await projectStore.loadProjects()

// 创建项目
const newProject = await projectStore.create({
  name: '新项目',
  description: '项目描述'
})

// 选择项目
projectStore.selectProject(newProject.id)

// 获取当前项目
const current = projectStore.currentProject

// 删除项目
await projectStore.deleteProject(projectId)
```

## 与后端 API 对接

前端类型定义与后端 Pydantic Schema 完全匹配:
- `Project` ↔️ `ProjectOut`
- `ProjectCreate` ↔️ `ProjectCreate`
- `ProjectUpdateForm` ↔️ `ProjectUpdate`

API 端点:
- `GET /api/v1/projects/` - 获取项目列表
- `POST /api/v1/projects/` - 创建项目
- `GET /api/v1/projects/{id}` - 获取单个项目
- `PUT /api/v1/projects/{id}` - 更新项目
- `DELETE /api/v1/projects/{id}` - 删除项目

## 下一步

前端逻辑层已完成，可以继续实现:
1. 项目管理 UI 组件 (Part 2.2)
2. 项目列表页面
3. 项目创建/编辑对话框
4. 项目选择器组件
