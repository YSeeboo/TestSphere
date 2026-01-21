"""应用配置模块 - 使用 Pydantic Settings 管理环境变量."""

from typing import Any
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基础配置
    APP_NAME: str = "ATP Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # CORS 配置
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="允许的跨域来源列表",
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # PostgreSQL 配置
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "atp_user"
    POSTGRES_PASSWORD: str = "atp_password"
    POSTGRES_DB: str = "atp_db"
    DATABASE_URL: PostgresDsn | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info: Any) -> str:
        """构建数据库连接字符串."""
        if isinstance(v, str) and v:
            return v
        
        data = info.data
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=data.get("POSTGRES_USER"),
                password=data.get("POSTGRES_PASSWORD"),
                host=data.get("POSTGRES_HOST"),
                port=data.get("POSTGRES_PORT"),
                path=data.get("POSTGRES_DB", ""),
            )
        )

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_URL: RedisDsn | None = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: str | None, info: Any) -> str:
        """构建 Redis 连接字符串."""
        if isinstance(v, str) and v:
            return v
        
        data = info.data
        password = data.get("REDIS_PASSWORD")
        
        if password:
            return str(
                RedisDsn.build(
                    scheme="redis",
                    username=None,
                    password=password,
                    host=data.get("REDIS_HOST"),
                    port=data.get("REDIS_PORT"),
                    path=str(data.get("REDIS_DB", 0)),
                )
            )
        else:
            return f"redis://{data.get('REDIS_HOST')}:{data.get('REDIS_PORT')}/{data.get('REDIS_DB', 0)}"

    # 数据库连接池配置
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # JWT 认证配置
    SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="JWT 签名密钥，生产环境必须修改为随机生成的密钥",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


# 全局配置实例
settings = Settings()
