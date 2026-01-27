# 项目管理功能说明

## 功能概述

项目管理功能允许用户创建、查看和管理多个测试项目。每个用户可以拥有多个项目，并可以在不同项目之间切换。

## 功能特性

### 1. 项目列表页 (`/projects`)

- **查看项目列表**: 显示当前用户创建的所有项目
- **创建新项目**: 通过弹窗表单创建新项目
- **进入项目**: 选择项目并进入仪表盘
- **删除项目**: 删除不需要的项目（需确认）

### 2. 当前项目状态管理

- **持久化存储**: 当前选中的项目 ID 存储在 `localStorage` 中，刷新页面后仍然保持
- **全局显示**: 在顶部导航栏显示当前项目名称
- **自动验证**: 如果当前项目不存在（被删除），自动清除选择状态

### 3. 路由守卫

- **项目检查**: 访问需要项目的页面（如仪表盘）时，自动检查是否已选择项目
- **自动重定向**: 如果未选择项目，自动重定向到项目管理页

## 文件结构

```
frontend/src/
├── api/
│   └── project.ts              # 项目 API 调用封装
├── stores/
│   └── project.ts              # 项目状态管理 (Pinia)
├── types/
│   └── project.ts              # 项目类型定义
├── views/
│   ├── project/
│   │   └── index.vue           # 项目列表页
│   ├── Dashboard.vue           # 仪表盘（显示当前项目信息）
│   └── Layout.vue              # 主布局（显示当前项目）
└── router/
    └── index.ts                # 路由配置（项目检查守卫）
```

## API 接口

### 获取项目列表
```typescript
GET /api/v1/projects/
Response: Project[]
```

### 创建项目
```typescript
POST /api/v1/projects/
Body: { name: string, description?: string }
Response: Project
```

### 获取单个项目
```typescript
GET /api/v1/projects/:id
Response: Project
```

### 更新项目
```typescript
PUT /api/v1/projects/:id
Body: { name?: string, description?: string }
Response: Project
```

### 删除项目
```typescript
DELETE /api/v1/projects/:id
Response: 204 No Content
```

## 数据模型

### Project 接口
```typescript
interface Project {
  id: number
  name: string
  description: string | null
  owner_id: number
  created_at: string
  updated_at: string
}
```

### ProjectCreateForm 接口
```typescript
interface ProjectCreateForm {
  name: string
  description?: string
}
```

## Store 状态管理

### State
- `list: Project[]` - 项目列表
- `currentProjectId: number | null` - 当前选中的项目 ID

### Getters
- `currentProject: Project | null` - 当前选中的项目对象

### Actions
- `fetchList()` - 获取项目列表
- `create(data)` - 创建新项目
- `remove(id)` - 删除项目
- `setCurrent(id)` - 设置当前项目
- `reset()` - 重置状态

## 使用流程

### 1. 首次登录
1. 用户登录成功后，尝试访问仪表盘 (`/dashboard`)
2. 路由守卫检测到未选择项目，自动重定向到 `/projects`
3. 用户在项目列表页创建或选择项目
4. 点击"进入项目"后，设置当前项目并跳转到仪表盘

### 2. 创建项目
1. 在项目列表页点击"新建项目"按钮
2. 填写项目名称（必填）和描述（可选）
3. 点击"确定"提交表单
4. 项目创建成功后，自动添加到列表顶部

### 3. 切换项目
1. 访问项目列表页 (`/projects`)
2. 点击目标项目的"进入项目"按钮
3. 系统设置新的当前项目并跳转到仪表盘

### 4. 删除项目
1. 在项目列表页点击"删除"按钮
2. 确认删除操作
3. 项目从列表中移除
4. 如果删除的是当前项目，自动清除当前项目选择

## 注意事项

1. **权限控制**: 用户只能查看、修改和删除自己创建的项目
2. **数据持久化**: 当前项目 ID 存储在 `localStorage`，清除浏览器数据会丢失
3. **自动清理**: 用户登出时，自动清除项目状态
4. **路由保护**: 需要项目的页面会自动检查并重定向
5. **表单验证**: 项目名称必填，长度限制 1-255 字符

## 扩展功能建议

1. **项目搜索**: 添加搜索框，支持按名称搜索项目
2. **项目排序**: 支持按创建时间、名称等排序
3. **项目分页**: 当项目数量较多时，添加分页功能
4. **项目统计**: 显示项目的测试用例数、执行次数等统计信息
5. **项目分享**: 支持将项目分享给其他用户（需要权限管理）
6. **项目归档**: 支持归档不活跃的项目
7. **批量操作**: 支持批量删除、导出项目

## 测试建议

### 单元测试
- 测试 Store 的各个 Action
- 测试 API 调用函数
- 测试路由守卫逻辑

### 集成测试
- 测试完整的创建项目流程
- 测试项目切换流程
- 测试删除项目流程
- 测试路由重定向逻辑

### E2E 测试
- 模拟用户完整操作流程
- 测试边界情况（无项目、网络错误等）
