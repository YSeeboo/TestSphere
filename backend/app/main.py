"""FastAPI 应用主入口."""

from contextlib import asynccontextmanager
import os
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.api import api_router
from app.db.session import async_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理.
    
    启动时执行初始化操作，关闭时执行清理操作.
    """
    # 启动时执行
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📊 Database: {settings.DATABASE_URL}")
    print(f"📦 Redis: {settings.REDIS_URL}")
    
    yield
    
    # 关闭时执行
    print("🛑 Shutting down application...")
    await async_engine.dispose()
    print("✅ Database connections closed")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="自动化测试平台后端服务",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# 配置静态文件目录（Allure 报告）
reports_dir = "/app/static/reports"
os.makedirs(reports_dir, exist_ok=True)
app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 注册 API 路由
app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


@app.get("/", summary="根路径", tags=["Root"])
async def root() -> dict[str, str]:
    """
    根路径接口.
    
    Returns:
        dict: 包含欢迎信息和 API 文档链接
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
