# 修复 projectStore.init() 错误

## 问题描述

运行前端应用后，浏览器控制台报错：

```
Vue Error: TypeError: projectStore.init is not a function
    at Layout.vue:59:16
```

## 原因分析

在之前修复循环依赖问题时，我们改进了 `projectStore` 的初始化机制：

**修复前（旧方式）：**
```typescript
// stores/project.ts
const currentProjectId = ref<number | null>(null)

function init() {
  const saved = localStorage.getItem(ACTIVE_PROJECT_KEY)
  if (saved) {
    const id = parseInt(saved, 10)
    if (!isNaN(id)) {
      currentProjectId.value = id
    }
  }
}

return { init, ... }
```

组件需要手动调用：
```typescript
// Layout.vue
onMounted(() => {
  projectStore.init()  // 手动初始化
})
```

**修复后（新方式）：**
```typescript
// stores/project.ts
function initProjectIdFromStorage(): number | null {
  const saved = localStorage.getItem(ACTIVE_PROJECT_KEY)
  if (saved) {
    const id = parseInt(saved, 10)
    return isNaN(id) ? null : id
  }
  return null
}

// 直接在定义时初始化
const currentProjectId = ref<number | null>(initProjectIdFromStorage())

// ❌ 不再导出 init 方法
```

但是 `Layout.vue` 中仍在调用已被移除的 `init()` 方法，导致运行时错误。

## 解决方案

### ✅ 已实施的修复

**修改文件：** `frontend/src/views/Layout.vue`

移除了 `onMounted` 钩子中对 `projectStore.init()` 的调用：

```typescript
// 修复前
import { ref, computed, onMounted } from 'vue'

onMounted(() => {
  projectStore.init()  // ❌ 调用已不存在的方法
})

// 修复后
import { ref, computed } from 'vue'

// projectStore 会在定义时自动初始化，不需要手动调用
// 移除了 onMounted 和 init() 调用
```

## 技术说明

### 为什么改进初始化机制？

**旧方式的问题：**
1. ❌ 需要手动调用 `init()`，容易忘记
2. ❌ 如果忘记调用，状态不会被恢复
3. ❌ 初始化时机不明确

**新方式的优势：**
1. ✅ 自动初始化，无需手动调用
2. ✅ Store 定义时立即恢复状态
3. ✅ 初始化时机明确（Store 创建时）
4. ✅ 符合 Vue 3 响应式系统最佳实践

### 初始化时机对比

```typescript
// 旧方式
const store = useProjectStore()        // Store 创建，currentProjectId = null
// ... 一段时间后 ...
onMounted(() => {
  store.init()                         // 从 localStorage 恢复值
})

// 新方式
const store = useProjectStore()        // Store 创建时立即从 localStorage 恢复值
// currentProjectId 已经有正确的值了
```

## 验证修复

修复后，应用应该能正常运行，不再出现错误。

### 验证步骤

1. **清理浏览器缓存**（如果之前有缓存）
   ```bash
   # 在浏览器开发者工具中
   Application -> Clear storage -> Clear site data
   ```

2. **刷新页面**
   - 按 F5 或 Cmd+R (macOS)
   - 检查控制台是否还有错误

3. **验证项目状态恢复**
   - 选择一个项目
   - 刷新页面
   - 检查项目是否仍被选中（显示在顶部导航栏）

## 相关修改

这个问题是之前修复循环依赖问题的后续影响：

**相关修复文档：**
- `docs/code_review_frontend_fixes.md` - 前端修复总结
  - 第 7 点：改进 Store 初始化机制

**相关文件：**
- `frontend/src/stores/project.ts` - Store 定义
- `frontend/src/views/Layout.vue` - 布局组件

## 最佳实践建议

### Store 初始化的推荐方式

对于需要从持久化存储（如 localStorage）恢复状态的 Store：

```typescript
// ✅ 推荐：定义时初始化
function initFromStorage(): number | null {
  // 初始化逻辑
  return savedValue
}

const state = ref(initFromStorage())

// ❌ 不推荐：需要手动调用的 init()
const state = ref(null)

function init() {
  state.value = getFromStorage()
}
```

### 何时使用手动 init()？

只在以下情况使用手动初始化：

1. **异步初始化**：需要从 API 获取初始数据
   ```typescript
   async function init() {
     const data = await fetchFromAPI()
     state.value = data
   }
   ```

2. **依赖外部条件**：初始化需要等待某些条件
   ```typescript
   function init(userId: number) {
     // 需要 userId 才能初始化
     state.value = loadUserData(userId)
   }
   ```

3. **重新初始化**：需要多次重置状态
   ```typescript
   function init() {
     // 重置到初始状态
     state.value = getInitialState()
   }
   ```

对于简单的从 localStorage 读取，使用定义时初始化即可。

## 故障排除

### 问题 1：刷新后项目没有恢复

**原因**：localStorage 可能被清除或值不正确。

**检查**：
```javascript
// 在浏览器控制台执行
localStorage.getItem('active_project_id')
```

**解决**：重新选择项目即可。

### 问题 2：仍然报错

**原因**：浏览器缓存了旧代码。

**解决**：
1. 硬刷新：Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (macOS)
2. 清除浏览器缓存
3. 重启开发服务器

### 问题 3：TypeScript 编译错误

**原因**：如果有其他地方引用了 `init` 方法。

**检查**：
```bash
cd frontend
npm run type-check
```

**解决**：移除所有对 `projectStore.init()` 的调用。

## 完成状态

- [x] 修改 Layout.vue，移除 init() 调用
- [x] 验证没有其他地方调用 init()
- [x] 添加注释说明新的初始化机制
- [x] 创建修复文档

---

**修复时间**：2026-01-29
**相关问题**：循环依赖修复的后续影响
**修复人员**：Claude Sonnet 4.5
