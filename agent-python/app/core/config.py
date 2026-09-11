from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_token: str = Field("change-me", validation_alias="AGENT_SERVICE_TOKEN")
    deepseek_api_key: str = Field("", validation_alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", validation_alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field("deepseek-chat", validation_alias="DEEPSEEK_MODEL")
    agent_timeout_seconds: float = Field(60.0, validation_alias="AGENT_TIMEOUT_SECONDS")
    max_topic_turns: int = Field(6, validation_alias="AGENT_MAX_TOPIC_TURNS")
    # 测评过程由本服务负责，所以它直接读写测评相关的表：发题快照、对话记忆、评分结果。
    # 用户、班级、题库的增删改仍然只发生在 Java 侧，这里只读题目和班级题库。
    db_host: str = Field("127.0.0.1", validation_alias="DB_HOST")
    db_port: int = Field(3306, validation_alias="DB_PORT")
    db_user: str = Field("root", validation_alias="DB_USERNAME")
    db_password: str = Field("", validation_alias="DB_PASSWORD")
    db_name: str = Field("ai_assessment", validation_alias="DB_NAME")
    # 设为 DEBUG 可以看到对话/收尾/评分的耗时与输入摘要
    log_level: str = Field("INFO", validation_alias="AGENT_LOG_LEVEL")
    # 单独打开时才会输出 openai/httpx 的底层 HTTP 报文（很吵，排查连不上时用）
    log_http: bool = Field(False, validation_alias="AGENT_LOG_HTTP")
    # 能力等级划档：逗号分隔的「最低分:等级:名称」，从高到低；留空用内置档位。
    # 例：ABILITY_LEVELS="90:L5:创新应用者,80:L4:人机协同专家,70:L3:应用进阶者,60:L2:工具使用者,0:L1:基础认知者"
    # 比赛现场要临时调档位时，改环境变量重启即可，不用碰代码。
    ability_levels: str = Field("", validation_alias="ABILITY_LEVELS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def model_configured(self) -> bool:
        return bool(self.deepseek_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
