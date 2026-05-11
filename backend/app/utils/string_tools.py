from __future__ import annotations
from hashlib import sha256


def build_database_url(
    *,
    db_engine: str,
    db_driver: str,
    db_host: str,
    db_port: int,
    db_name: str,
    db_user: str,
    db_password: str,
    db_sqlite_path: str,
) -> str:
    """拼接数据库连接URL字符串。

    Args:
        db_engine: 数据库引擎类型。
        db_driver: 数据库驱动名称。
        db_host: 数据库主机地址。
        db_port: 数据库端口。
        db_name: 数据库名称。
        db_user: 数据库用户名。
        db_password: 数据库密码。
        db_sqlite_path: SQLite 数据文件路径。

    Returns:
        str: 可用于 SQLModel 的数据库连接 URL。
    """
    if db_engine.lower() == "sqlite":
        return f"{db_engine}+{db_driver}:///{db_sqlite_path}"

    return f"{db_engine.lower()}+{db_driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def hash_password(password: str) -> str:
    """对明文密码进行 SHA-256 摘要计算。

    Args:
        password: 待处理的明文密码。

    Returns:
        str: 十六进制格式的密码摘要。
    """
    return sha256(password.encode("utf-8")).hexdigest()