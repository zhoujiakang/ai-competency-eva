"""数据库访问层。

测评过程归本服务负责，所以这里直接连 MySQL：发题快照、对话记忆、评分结果都写库，
题目和班级题库只读。用户、班级、题库的增删改仍然只在 Java 侧发生。
"""

from app.db.pool import Database
from app.db.repository import AssessmentRepository

__all__ = ["Database", "AssessmentRepository"]
