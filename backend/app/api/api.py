"""API 路由汇总."""

from fastapi import APIRouter

from app.api.endpoints import auth, health, users

# 创建 API v1 路由
api_router = APIRouter()

# 注册各个端点路由
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
