# 🚀 ATP - 分布式自动化测试平台 (Automation Test Platform)

> 基于 FastAPI + Celery + Docker 的企业级自动化测试解决方案。
> 实现了测试用例的 GitOps 管理、容器化隔离执行及全链路日志追踪。

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Vue](https://img.shields.io/badge/Vue-3.x-green)

## ✨ 核心特性

- **🛡️ 隔离执行**: 采用 "One-Task-One-Container" 架构，基于 Docker 实现环境的绝对纯净。
- **🔄 GitOps 同步**: 自动解析 Git 仓库中的 Pytest 用例，无需在 Web 端重复编写代码。
- **📊 智能报告**: 集成 Allure 历史趋势，支持失败用例的 **AI 根因分析** (Based on LLM)。
- **🔐 生产熔断**: 独创的环境锁机制，自动拦截针对 Production 环境的高危写操作。

## 🛠️ 技术栈

- **后端**: Python, FastAPI, Celery, SQLAlchemy
- **执行引擎**: Docker SDK for Python
- **数据库**: PostgreSQL, Redis
- **前端**: Vue3, Element Plus (或 AntD)

## 📂 快速开始 (Quick Start)

### 1. 启动服务

```bash
# 需提前安装 Docker 和 Docker Compose
docker-compose up -d
```

### 2.访问控制台

浏览器打开 http://localhost:8080，默认账号 admin / admin

## 📄 文档

详细的产品需求文档与架构设计请见：PRD v0.1.0

## ⚖️ License

MIT License
