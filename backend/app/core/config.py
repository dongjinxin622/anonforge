from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 提取项目工程的根目录路径，拼接.env的路径并加载.env中的环境配置
BASE_DIR = Path(__file__).resolve().parents[3]

# 拼接路径
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE, override=False)


# frozen=True 冻结属性值，不允许配置类Settings实例化以后，被其他地方的程序修改属性值
@dataclass(frozen=True)
class Settings(object):
    """项目运行时配置对象。"""
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "App"))
    app_description: str = field(default_factory=lambda: os.getenv("APP_DESCRIPTION", "App description"))
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    api_prefix: str = field(default_factory=lambda: os.getenv("API_PREFIX", "/api"))
    oss_root: str = field(default_factory=lambda: os.getenv("OSS_ROOT", "./data/oss"))
    db_engine: str = field(default_factory=lambda: os.getenv("DB_ENGINE", "postgres"))
    db_driver: str = field(default_factory=lambda: os.getenv("DB_DRIVER", "psycopg"))
    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST", "127.0.0.1"))
    db_port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "anonforge"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", "anonforge"))
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", "anonforge"))
    db_sqlite_path: str = field(default_factory=lambda: os.getenv("DB_SQLITE_PATH", "./data/app.db"))
    tz: str = field(default_factory=lambda: os.getenv("TZ", "Asia/Shanghai"))
    postgres_image: str = field(default_factory=lambda: os.getenv("POSTGRES_IMAGE", "postgres:18-alpine"))
    postgres_container_name: str = field(default_factory=lambda: os.getenv("POSTGRES_CONTAINER_NAME", "anonforge_dev_postgres"))
    postgres_host_port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_HOST_PORT", "5432")))
    db_data_path: str = field(default_factory=lambda: os.getenv("DB_DATA_PATH", "./postgres/data"))
    db_healthcheck_interval: str = field(default_factory=lambda: os.getenv("DB_HEALTHCHECK_INTERVAL", "10s"))
    db_healthcheck_timeout: str = field(default_factory=lambda: os.getenv("DB_HEALTHCHECK_TIMEOUT", "5s"))
    db_healthcheck_retries: int = field(default_factory=lambda: int(os.getenv("DB_HEALTHCHECK_RETRIES", "5")))

    redis_host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "127.0.0.1"))
    redis_port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    redis_db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    redis_container_name: str = field(default_factory=lambda: os.getenv("REDIS_CONTAINER_NAME", "anonforge_dev_redis"))
    redis_data_path: str = field(default_factory=lambda: os.getenv("REDIS_DATA_PATH", "./redis/data"))
    redis_healthcheck_interval: str = field(default_factory=lambda: os.getenv("REDIS_HEALTHCHECK_INTERVAL", "10s"))
    redis_healthcheck_timeout: str = field(default_factory=lambda: os.getenv("REDIS_HEALTHCHECK_TIMEOUT", "5s"))
    redis_healthcheck_retries: int = field(default_factory=lambda: int(os.getenv("REDIS_HEALTHCHECK_RETRIES", "3")))

    redis_token_key_prefix: str = field(default_factory=lambda: os.getenv("REDIS_TOKEN_KEY_PREFIX", "auth:token:"))
    algorithm: str = field(default_factory=lambda: os.getenv("ALGORITHM", "HS256"))
    access_token_expire_seconds: int = field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "900")))
    refresh_token_expire_seconds: int = field(default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_SECONDS", "604800")))
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret-key"))

    user_default_admin_name: str = field(default_factory=lambda: os.getenv("USER_DEFAULT_ADMIN_NAME", "admin"))
    user_default_admin_password: str = field(default_factory=lambda: os.getenv("USER_DEFAULT_ADMIN_PASSWORD", "admin123"))


settings = Settings()