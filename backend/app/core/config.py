"""应用配置模块 - 使用 Pydantic Settings 管理环境变量."""

import secrets
from typing import Any
from pydantic import Field, PostgresDsn, RedisDsn, field_validator, model_validator
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
        ...,  # 强制从环境变量读取，不提供默认值
        description="JWT 签名密钥，必须通过环境变量设置（至少 32 字符）",
        min_length=32,
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        """验证安全相关配置."""
        # 检查是否使用了不安全的示例密钥
        INSECURE_KEYS = {
            "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
            "your-secret-key-here",
            "secret",
            "changeme",
        }
        
        if self.SECRET_KEY in INSECURE_KEYS:
            raise ValueError(
                "检测到不安全的 SECRET_KEY！\n"
                "请在环境变量中设置安全的密钥。\n"
                f"生成新密钥的命令: python -c 'import secrets; print(secrets.token_hex(32))'\n"
                "或使用 openssl: openssl rand -hex 32"
            )
        
        # 在生产环境强制检查密钥强度
        if not self.DEBUG and len(self.SECRET_KEY) < 32:
            raise ValueError(
                f"生产环境的 SECRET_KEY 长度必须至少 32 字符，当前长度: {len(self.SECRET_KEY)}"
            )
        
        return self


# 全局配置实例
settings = Settings()
