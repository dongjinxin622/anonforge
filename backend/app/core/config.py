from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 提取项目工程的根目录路径，拼接.env的路径并加载.env中的环境配置
BASE_DIR = Path(__file__).resolve().parents[3]

# BASE_DIR 解析路径示例:
#   backend/app/core/config.py
#   -> parents[0]: backend/app/core
#   -> parents[1]: backend/app
#   -> parents[2]: backend
#   -> parents[3]: 项目根目录
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
    db_engine: str = field(default_factory=lambda: os.getenv("DB_ENGINE", "mysql"))
    db_driver: str = field(default_factory=lambda: os.getenv("DB_DRIVER", "aiomysql"))
    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST", "8.147.69.101"))
    db_port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "3306")))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "anonforge"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", "root"))
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "mysql+aiomysql://root:@8.147.69.101:3306/anonforge"))
    tz: str = field(default_factory=lambda: os.getenv("TZ", "Asia/Shanghai"))

settings = Settings()