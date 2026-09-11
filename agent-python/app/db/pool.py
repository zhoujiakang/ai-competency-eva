"""MySQL 连接池：整个服务里唯一创建连接的地方。"""

import logging
from contextlib import asynccontextmanager

import aiomysql

from app.core.config import Settings

logger = logging.getLogger("agent.db")


class Database:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._pool: aiomysql.Pool | None = None

    async def connect(self) -> None:
        s = self._settings
        try:
            self._pool = await aiomysql.create_pool(
                host=s.db_host,
                port=s.db_port,
                user=s.db_user,
                password=s.db_password,
                db=s.db_name,
                charset="utf8mb4",
                autocommit=True,
                minsize=1,
                maxsize=5,
            )
        except Exception as exc:
            # 连不上库时服务仍然起得来，健康检查可用；测评接口会明确报错。
            self._pool = None
            logger.warning("database unavailable, assessment endpoints are disabled: %s", exc)

    async def close(self) -> None:
        if self._pool is None:
            return
        self._pool.close()
        await self._pool.wait_closed()
        self._pool = None

    @asynccontextmanager
    async def cursor(self):
        """拿一个字典游标，查询结果按列名取值。"""
        if self._pool is None:
            raise RuntimeError("database pool is not connected")
        async with self._pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                yield cursor
