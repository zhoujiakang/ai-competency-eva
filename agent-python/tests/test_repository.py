"""仓库层里最容易出错的一段：写对话消息时的序号分配。

不连数据库，用一个假游标把「并发撞号」这个场景精确复现出来——真实并发很难在
单测里稳定触发，但它的表现就是第一条 INSERT 抛 1062 唯一键冲突。
"""

import aiomysql
import anyio
import pytest

from app.db.repository import MESSAGE_INSERT_ATTEMPTS, AssessmentRepository


class FakeCursor:
    def __init__(self, db):
        self._db = db
        self.lastrowid = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def execute(self, sql, params):
        self._db.attempts.append(params)
        if self._db.remaining_failures > 0:
            self._db.remaining_failures -= 1
            raise aiomysql.IntegrityError(self._db.error_code, "Duplicate entry for key uk_message_sequence")
        self.lastrowid = len(self._db.attempts)


class FakeDatabase:
    """只实现仓库用到的 cursor()；remaining_failures 表示前几次 INSERT 抛错。"""

    def __init__(self, failures=0, error_code=1062):
        self.remaining_failures = failures
        self.error_code = error_code
        self.attempts = []

    def cursor(self):
        return FakeCursor(self)


def append(db):
    async def run():
        return await AssessmentRepository(db).append_message(1, 11, "ai", "题干")

    return anyio.run(run)


def test_a_duplicate_sequence_is_retried_and_succeeds():
    db = FakeDatabase(failures=1)

    message = append(db)

    assert len(db.attempts) == 2                 # 第一次撞号，重试后成功
    assert message["content"] == "题干"
    assert message["sender_type"] == "ai"
    # 序号由数据库分配，返回值不需要回读；调用方只拿它维护本回合的内存历史
    assert message["sequence_no"] is None


def test_retry_gives_up_after_the_configured_attempts():
    db = FakeDatabase(failures=MESSAGE_INSERT_ATTEMPTS)

    with pytest.raises(aiomysql.IntegrityError):
        append(db)

    assert len(db.attempts) == MESSAGE_INSERT_ATTEMPTS


def test_errors_that_are_not_races_propagate_immediately():
    """比如表不存在 / 语法错误：重试没有意义，必须原样抛出去。"""
    db = FakeDatabase(failures=1, error_code=1146)

    with pytest.raises(aiomysql.IntegrityError):
        append(db)

    assert len(db.attempts) == 1
