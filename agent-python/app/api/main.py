"""FastAPI 应用装配。

这一层只做三件事：建应用、挂路由、在启动时把 Agent 放进 app.state。
任何业务逻辑都不应该写在这里。
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.agent import AssessmentAgent
from app.api.routes import agent, assessments, health
from app.core.config import get_settings
from app.assessment import AssessmentFlow
from app.db import AssessmentRepository, Database


NOISY_LOGGERS = ("httpx", "httpcore", "openai", "urllib3", "asyncio")


def _configure_logging(level: str, log_http: bool = False) -> None:
    """配置根日志。

    uvicorn 只配置自己的 logger，不碰 root，所以 agent.* 的日志默认不会输出。
    这里显式配置一次，用 AGENT_LOG_LEVEL=DEBUG 就能看到每个能力的调用详情。

    openai / httpx 这些第三方库的 DEBUG 会把完整请求报文都打出来，
    默认压到 WARNING；确实要看底层报文时再开 AGENT_LOG_HTTP=1。
    """
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    )
    if not log_http:
        for name in NOISY_LOGGERS:
            logging.getLogger(name).setLevel(logging.WARNING)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        settings = get_settings()
        _configure_logging(settings.log_level, settings.log_http)
        database = Database(settings)
        await database.connect()
        try:
            application.state.agent = AssessmentAgent(settings)
            application.state.database = database
            application.state.flow = AssessmentFlow(application.state.agent, AssessmentRepository(database), settings)
            yield
        finally:
            await database.close()

    application = FastAPI(title="AI Assessment Agent", version="1.0.0", lifespan=lifespan)
    application.include_router(health.router)
    application.include_router(agent.router)
    application.include_router(assessments.router)
    return application


app = create_app()
