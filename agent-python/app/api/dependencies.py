"""FastAPI 依赖：鉴权和 Agent 实例的获取。

测试时可以用 app.dependency_overrides 把 get_agent 换成假实现，
不调用真实模型也能验证 HTTP 层的契约。
"""

from fastapi import Header, HTTPException, Request, status

from app.agent import AssessmentAgent
from app.assessment import AssessmentFlow
from app.core.config import get_settings


def require_service_token(authorization: str | None = Header(default=None)):
    """校验 Java 传来的服务令牌；Agent 不接收学生登录令牌。"""
    expected = get_settings().service_token
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not authorization or supplied != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid service token")


def get_agent(request: Request) -> AssessmentAgent:
    """从应用状态取 Agent 实例（在 lifespan 中创建）。"""
    return request.app.state.agent


def get_flow(request: Request) -> AssessmentFlow:
    """从应用状态取测评流程（在 lifespan 中创建）。"""
    return request.app.state.flow
