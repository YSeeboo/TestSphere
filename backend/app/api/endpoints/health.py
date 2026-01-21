"""健康检查端点 - 检测数据库和 Redis 连接状态."""

from typing import Any, AsyncGenerator

from app.core.config import settings
from app.db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_redis() -> AsyncGenerator[Redis, None]:
    """获取 Redis 连接."""
    redis = Redis.from_url(
        str(settings.REDIS_URL),
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield redis
    finally:
        await redis.aclose()


@router.get("", summary="健康检查", tags=["System"])
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict[str, Any]:
    """
    健康检查接口 - 验证数据库和 Redis 连接状态.
    
    Returns:
        dict: 包含服务状态信息的字典
        
    Raises:
        HTTPException: 当数据库或 Redis 连接失败时
    """
    health_status: dict[str, Any] = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "unknown",
        "redis": "unknown",
    }

    # 检查数据库连接
    try:
        result = await db.execute(text("SELECT 1"))
        row = result.scalar()
        if row == 1:
            health_status["database"] = "connected"
        else:
            health_status["database"] = "error"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # 检查 Redis 连接
    try:
        pong = await redis.ping()
        if pong:
            health_status["redis"] = "connected"
        else:
            health_status["redis"] = "error"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # 如果任何服务不健康，返回 503 状态码
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status,
        )

    return health_status


@router.get("/health/ready", summary="就绪检查", tags=["System"])
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    """
    就绪检查接口 - 用于 Kubernetes readiness probe.
    
    Returns:
        dict: 简单的就绪状态
        
    Raises:
        HTTPException: 当服务未就绪时
    """
    try:
        # 快速检查数据库
        await db.execute(text("SELECT 1"))
        # 快速检查 Redis
        await redis.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not ready", "error": str(e)},
        )


@router.get("/health/live", summary="存活检查", tags=["System"])
async def liveness_check() -> dict[str, str]:
    """
    存活检查接口 - 用于 Kubernetes liveness probe.
    
    仅检查应用进程是否存活，不检查依赖服务.
    
    Returns:
        dict: 简单的存活状态
    """
    return {"status": "alive"}
