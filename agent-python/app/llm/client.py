"""模型客户端：整个服务里唯一直接依赖大模型厂商的地方。

只做三件事，别的都不管：

    text()   一次性拿到一段文本
    stream() 逐片段拿到文本
    json()   拿到结构化 JSON，并用 Pydantic 校验

想换模型或换厂商（DeepSeek → OpenAI → 本地 vLLM → 通义……），只改这个文件。
接口是 OpenAI 兼容协议，多数情况下只要改 base_url 和模型名。

刻意不使用 LangChain：调用方式就是官方 SDK 的最普通用法，
读代码时不需要先理解任何框架概念。
"""

import json
import re
from collections.abc import AsyncIterator
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.core.exceptions import AgentNotConfigured, ModelReplyError

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def extract_json(text: str) -> str:
    """从模型输出里抠出 JSON 对象。

    模型经常加 ```json 包裹，或前后带一句解释，这里统一处理掉。
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end < start:
        raise ModelReplyError(f"模型输出里没有 JSON 对象：{text[:120]}")
    return cleaned[start : end + 1]


def parse_arguments(raw: str | None) -> dict:
    """把工具调用的参数文本解析成字典；模型偶尔给空串或半个 JSON，一律当空参数。"""
    try:
        parsed = json.loads(raw or "{}")
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


class LlmClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: AsyncOpenAI | None = None

    @property
    def configured(self) -> bool:
        return self.settings.model_configured

    @property
    def source_name(self) -> str:
        """写进响应的来源标识，接口用它区分回复出自哪个模型。"""
        return "deepseek"

    def _sdk(self) -> AsyncOpenAI:
        if not self.configured:
            raise AgentNotConfigured("DEEPSEEK_API_KEY is not configured")
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.settings.deepseek_api_key,
                base_url=self.settings.deepseek_base_url.rstrip("/"),
                timeout=self.settings.agent_timeout_seconds,
                max_retries=1,
            )
        return self._client

    @staticmethod
    def _messages(system: str, user: str) -> list[dict[str, str]]:
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    async def text(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.4,
        max_tokens: int | None = None,
    ) -> str:
        """一次性返回完整文本。"""
        response = await self._sdk().chat.completions.create(
            model=self.settings.deepseek_model,
            messages=self._messages(system, user),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (response.choices[0].message.content or "").strip()

    async def stream(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.4,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """逐片段返回文本，供 SSE 直接转发给浏览器。"""
        stream = await self._sdk().chat.completions.create(
            model=self.settings.deepseek_model,
            messages=self._messages(system, user),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for event in stream:
            if not event.choices:
                continue
            content = event.choices[0].delta.content
            if content:
                yield content

    async def call_tool(
        self,
        *,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str | dict = "required",
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> dict | None:
        """非流式的「让模型做个决定」：必须挑一个工具，返回它的第一个调用。

        刻意不流式、也不产出正文。模型的决策和它要说给学生听的话必须是两件事：
        合在一次调用里，正文是边流边发的，而工具调用要到这次响应结束才完整，
        等拿到决策时话已经说出去了——说出去的话收不回来，状态就只能跟着错。
        分开之后，动作先定，话再按动作生成，两者不可能矛盾。

        返回 {id, name, arguments, arguments_text}；模型没调用任何工具时返回 None。
        """
        response = await self._sdk().chat.completions.create(
            model=self.settings.deepseek_model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        calls = response.choices[0].message.tool_calls or []
        if not calls:
            return None
        call = calls[0]
        raw = call.function.arguments or "{}"
        return {
            "id": call.id,
            "name": call.function.name,
            "arguments_text": raw,
            "arguments": parse_arguments(raw),
        }

    async def json(
        self,
        *,
        system: str,
        user: str,
        schema: type[SchemaT],
        temperature: float = 0.0,
        attempts: int = 2,
    ) -> SchemaT:
        """返回结构化结果；解析失败会重试，仍失败则抛 ModelReplyError。"""
        last_error: Exception | None = None
        for _ in range(attempts):
            raw = await self.text(system=system, user=user, temperature=temperature)
            try:
                return schema.model_validate_json(extract_json(raw))
            except (ValidationError, ValueError) as exc:
                last_error = exc
        raise ModelReplyError(f"模型没有返回合法 JSON：{last_error}")
