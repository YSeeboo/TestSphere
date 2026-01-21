# ATP Frontend

自动化测试平台（Automated Test Platform）前端应用。

## 技术栈

- **框架**: Vue 3.4+
- **构建工具**: Vite 5.0+
- **语言**: TypeScript
- **UI 库**: Element Plus 2.5+
- **状态管理**: Pinia 2.1+
- **HTTP 客户端**: Axios 1.6+
- **路由**: Vue Router 4.2+

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
# 或使用 pnpm/yarn
# pnpm install
# yarn install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产构建

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── api/                 # API 接口定义
│   │   └── health.ts       # 健康检查接口
│   ├── assets/             # 静态资源
│   ├── components/         # 可复用组件
│   ├── router/             # 路由配置
│   │   └── index.ts
│   ├── stores/             # Pinia 状态管理
│   │   └── counter.ts      # 示例 store
│   ├── styles/             # 全局样式
│   │   └── index.scss
│   ├── utils/              # 工具函数
│   │   └── request.ts      # Axios 封装
│   ├── views/              # 页面组件
│   │   ├── Home.vue
│   │   └── About.vue
│   ├── App.vue             # 根组件
│   ├── main.ts             # 应用入口
│   └── vite-env.d.ts       # TypeScript 类型定义
├── index.html              # HTML 模板
├── vite.config.ts          # Vite 配置
├── tsconfig.json           # TypeScript 配置
├── package.json            # 依赖管理
└── README.md
```

## 开发规范

详见项目根目录的 `.cursorrules` 文件。

### 关键规范

✅ **Composition API**: 始终使用 `<script setup lang="ts">`  
✅ **TypeScript**: 严格类型检查  
✅ **Element Plus**: 使用 ElMessage、ElNotification 进行用户反馈  
✅ **Pinia**: 使用 setup 函数风格（function style）  
✅ **代码风格**: 清晰的中文注释，遵循 ESLint 规则  

## 配置说明

### Vite 配置

- **开发服务器**: 端口 5173
- **API 代理**: `/api` -> `http://localhost:8000`
- **路径别名**: `@` -> `src/`

### 环境变量

开发环境（`.env.development`）:

```bash
VITE_APP_TITLE=ATP - 自动化测试平台
VITE_APP_BASE_API=/api/v1
VITE_APP_PORT=5173
```

生产环境（`.env.production`）:

```bash
VITE_APP_TITLE=ATP - 自动化测试平台
VITE_APP_BASE_API=/api/v1
```

## 功能特性

### 已实现

- ✅ Axios 请求封装（请求/响应拦截、错误处理）
- ✅ Element Plus 自动导入
- ✅ Vue Router 路由配置
- ✅ Pinia 状态管理
- ✅ TypeScript 严格类型检查
- ✅ 健康检查接口集成
- ✅ 响应式布局

### 待实现

根据 `docs/Frontend_Design_v0.1.0.md` 继续开发：

- [ ] 用户认证与授权
- [ ] 测试用例管理
- [ ] 测试执行与监控
- [ ] 测试报告展示
- [ ] 系统配置管理

## 常用命令

```bash
# 开发
npm run dev              # 启动开发服务器
npm run build            # 构建生产版本
npm run preview          # 预览生产构建

# 代码质量
npm run type-check       # TypeScript 类型检查
npm run lint             # ESLint 代码检查
```

## API 接口

### 基础配置

- **Base URL**: `/api/v1`
- **代理目标**: `http://localhost:8000`

### 健康检查接口

```typescript
import { getHealth } from '@/api/health'

// 获取健康状态
const health = await getHealth()
// 返回: { status, service, version, database, redis }
```

## 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 故障排查

### 无法连接后端

1. 确保后端服务已启动: `http://localhost:8000`
2. 检查 Vite 代理配置: `vite.config.ts`
3. 查看浏览器控制台错误信息

### 类型错误

1. 运行 `npm run type-check` 检查类型错误
2. 确保 `tsconfig.json` 配置正确
3. 检查自动生成的类型文件: `src/auto-imports.d.ts`, `src/components.d.ts`

### 依赖安装失败

```bash
# 清除缓存
rm -rf node_modules package-lock.json
npm cache clean --force

# 重新安装
npm install
```

## 参考文档

- [Vue 3 文档](https://cn.vuejs.org/)
- [Vite 文档](https://cn.vitejs.dev/)
- [Element Plus 文档](https://element-plus.org/zh-CN/)
- [Pinia 文档](https://pinia.vuejs.org/zh/)
- [Vue Router 文档](https://router.vuejs.org/zh/)
- [TypeScript 文档](https://www.typescriptlang.org/)

## 许可证

MIT
