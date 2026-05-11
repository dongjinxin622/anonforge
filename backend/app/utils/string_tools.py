from __future__ import annotations

from urllib.parse import quote_plus


def build_database_url(
    db_engine: str,
    db_driver: str,
    db_host: str,
    db_port: int,
    db_name: str,
    db_user: str,
    db_password: str,
) -> str:
    """根据各字段拼装数据库连接 URL，对密码中的特殊字符做 URL 编码。

    Args:
        db_engine: 数据库引擎 (mysql, postgresql, sqlite 等)
        db_driver: 数据库驱动 (aiomysql, psycopg, pysqlite 等)
        db_host: 主机地址
        db_port: 端口号
        db_name: 数据库名称
        db_user: 用户名
        db_password: 密码

    Returns:
        str: 数据库连接 URL
    """
    if db_engine == "sqlite":
        return f"sqlite:///{db_name}"

    encoded_password = quote_plus(db_password)
    return (
        f"{db_engine}+{db_driver}://"
        f"{db_user}:{encoded_password}@"
        f"{db_host}:{db_port}/"
        f"{db_name}"
    )