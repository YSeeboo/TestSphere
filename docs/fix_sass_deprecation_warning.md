# 修复 Dart Sass 废弃警告

## 问题描述

运行 `npm run dev` 时出现以下警告：

```
Deprecation Warning [legacy-js-api]: The legacy JS API is deprecated and will be removed in Dart Sass 2.0.0.
```

## 原因分析

这个警告是因为项目使用了传统的 `sass` 包，它使用了 Dart Sass 的传统 JavaScript API。这个 API 将在 Dart Sass 2.0.0 中被移除。

## 解决方案

### ✅ 已实施的修复

我已经应用了以下修复：

1. **替换 sass 包为 sass-embedded**
   - 将 `sass: ^1.69.0` 替换为 `sass-embedded: ^1.79.0`
   - `sass-embedded` 使用 Dart Sass 的嵌入式协议，性能更好且完全支持现代 API

2. **配置 Vite 使用现代 Sass API**
   - 在 `vite.config.ts` 中添加 CSS 预处理器配置
   - 明确指定使用 `modern-compiler` API

### 📝 修改的文件

1. **frontend/package.json**
   ```json
   {
     "devDependencies": {
       "sass-embedded": "^1.79.0"  // 替代 "sass": "^1.69.0"
     }
   }
   ```

2. **frontend/vite.config.ts**
   ```typescript
   export default defineConfig({
     // ...其他配置
     css: {
       preprocessorOptions: {
         scss: {
           // 使用现代 Sass API
           api: 'modern-compiler',
         },
       },
     },
   })
   ```

## 🚀 应用修复

请执行以下步骤应用修复：

### 1. 清理旧依赖

```bash
cd frontend
rm -rf node_modules package-lock.json
```

### 2. 重新安装依赖

```bash
npm install
```

### 3. 验证修复

```bash
npm run dev
```

如果修复成功，你将不再看到 Dart Sass 的废弃警告。

## 🔍 验证清单

- [ ] 删除 `node_modules` 和 `package-lock.json`
- [ ] 运行 `npm install` 重新安装依赖
- [ ] 运行 `npm run dev` 启动开发服务器
- [ ] 确认控制台没有 Dart Sass 警告
- [ ] 测试样式是否正常显示

## 📚 技术说明

### sass vs sass-embedded

| 特性 | sass | sass-embedded |
|------|------|---------------|
| 实现 | Pure JavaScript | Dart Sass 嵌入式协议 |
| 性能 | 较慢 | 更快（接近原生 Dart Sass） |
| API | 传统 + 现代 | 仅现代 API |
| 未来兼容性 | ⚠️ 传统 API 将被废弃 | ✅ 完全支持 |
| 包大小 | 较大 | 较小 |

### modern-compiler API

Vite 5.4+ 支持 Sass 的现代编译器 API，主要优势：

- **更快的编译速度**：使用现代编译器架构
- **更好的错误消息**：提供更清晰的错误提示
- **完整的 Sass 功能支持**：支持所有现代 Sass 特性
- **未来兼容性**：与 Dart Sass 2.0+ 兼容

## ⚙️ 备选方案（如果主方案不适用）

如果由于某些原因无法使用 `sass-embedded`，可以尝试以下备选方案：

### 方案 2：静默警告（不推荐）

只是隐藏警告，不解决根本问题：

```typescript
// vite.config.ts
export default defineConfig({
  css: {
    preprocessorOptions: {
      scss: {
        silenceDeprecations: ['legacy-js-api'],
      },
    },
  },
})
```

**不推荐原因**：只是隐藏问题，Dart Sass 2.0 发布后仍会出现兼容性问题。

### 方案 3：降级 Vite（不推荐）

使用不支持现代 API 的旧版本 Vite：

```json
{
  "devDependencies": {
    "vite": "^4.5.0"
  }
}
```

**不推荐原因**：失去 Vite 5 的新特性和性能改进。

## 🐛 故障排除

### 问题 1：安装 sass-embedded 失败

**原因**：某些系统上可能需要额外的构建工具。

**解决**：
```bash
# macOS
xcode-select --install

# Linux (Ubuntu/Debian)
sudo apt-get install build-essential

# Linux (CentOS/Fedora)
sudo yum groupinstall "Development Tools"
```

### 问题 2：样式没有生效

**原因**：缓存问题。

**解决**：
```bash
# 清理 Vite 缓存
rm -rf frontend/node_modules/.vite

# 重新启动
npm run dev
```

### 问题 3：其他 Node 警告

如果还有其他警告，可能来自其他依赖。可以尝试升级相关依赖：

```bash
npm update
```

## 📖 参考资料

- [Dart Sass: Breaking Change: Legacy JS API](https://sass-lang.com/documentation/breaking-changes/legacy-js-api/)
- [Vite: CSS Pre-processors](https://vitejs.dev/config/shared-options.html#css-preprocessoroptions)
- [sass-embedded GitHub](https://github.com/sass/embedded-host-node)

## ✅ 完成状态

- [x] 修改 package.json
- [x] 修改 vite.config.ts
- [x] 创建修复文档
- [ ] 用户执行：清理依赖
- [ ] 用户执行：重新安装
- [ ] 用户执行：验证修复

---

**修复时间**：2026-01-29
**修复人员**：Claude Sonnet 4.5
