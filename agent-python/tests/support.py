"""测试用的假实现与构造器：让节点、图、门面都能在不联网的情况下被测试。"""

import json
from collections.abc import AsyncIterator, Sequence
from typing import Any

from app.agent.actions import ASK_FOLLOWUP
from app.core.config import Settings
from app.core.exceptions import ModelReplyError
from app.domain.schemas import Candidate, DialogueRequest, Message
from app.tools.question_selection import EngineContext


class FakeLlmClient:
    """假的模型客户端：**每个方法各自按调用顺序回放脚本**。

    一个回合是「决策 + 发言」两次调用，分开给脚本比按全局顺序排更好读：

        replies      stream() / text() 依次返回的内容；str 一次吐完，list[str] 逐段吐
        decisions    call_tool() 依次返回的工具名；None 表示这次不调用工具
        json_result  json() 返回的模型实例（没有给就报错，避免测试里悄悄走偏）

    每次调用都会记进 calls，方便断言提示词里到底塞了什么。
    """

    def __init__(self, replies: Sequence[Any] | None = None,
                 decisions: Sequence[str | None] | None = None, json_result: Any = None):
        self._replies = list(replies or ["默认回复"])
        self._decisions = list(decisions or [ASK_FOLLOWUP])
        self._json_result = json_result
        self.calls: list[dict[str, Any]] = []
        self._reply_index = 0
        self._decision_index = 0

    @property
    def configured(self) -> bool:
        return True

    @property
    def source_name(self) -> str:
        return "fake"

    def _next_reply(self) -> Any:
        item = self._replies[min(self._reply_index, len(self._replies) - 1)]
        self._reply_index += 1
        return item

    def _next_decision(self) -> str | None:
        item = self._decisions[min(self._decision_index, len(self._decisions) - 1)]
        self._decision_index += 1
        return item

    def _record(self, kind: str, system: str, user: str, **extra) -> None:
        self.calls.append({"kind": kind, "system": system, "user": user, **extra})

    async def text(self, *, system: str, user: str, temperature: float = 0.4, max_tokens: int | None = None) -> str:
        self._record("text", system, user, temperature=temperature, max_tokens=max_tokens)
        reply = self._next_reply()
        return "".join(reply) if isinstance(reply, list) else reply

    async def stream(self, *, system: str, user: str, temperature: float = 0.4, max_tokens: int | None = None) -> AsyncIterator[str]:
        self._record("stream", system, user, temperature=temperature, max_tokens=max_tokens)
        reply = self._next_reply()
        for chunk in reply if isinstance(reply, list) else [reply]:
            yield chunk

    async def call_tool(
        self,
        *,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str | dict = "required",
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> dict | None:
        self.calls.append({
            "kind": "tool",
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
        })
        name = self._next_decision()
        if name is None:
            return None
        arguments = {"reason": "测试脚本指定的理由"}
        return {
            "id": "call_0",
            "name": name,
            "arguments_text": json.dumps(arguments, ensure_ascii=False),
            "arguments": arguments,
        }

    async def json(self, *, system: str, user: str, schema, temperature: float = 0.0, attempts: int = 2):
        self._record("json", system, user, temperature=temperature)
        if self._json_result is None:
            raise ModelReplyError("测试没有提供 json_result")
        return self._json_result


def decision_prompt(call: dict) -> tuple[str, str]:
    """从一次 call_tool 调用里取出 (system, user) 文本，方便断言提示词内容。"""
    messages = call["messages"]
    system = next((m.get("content") or "" for m in messages if m["role"] == "system"), "")
    user = next((m.get("content") or "" for m in messages if m["role"] == "user"), "")
    return system, user


def settings(**overrides) -> Settings:
    values = {"deepseek_api_key": "test-key", "max_topic_turns": 6}
    values.update(overrides)
    return Settings(**values)


def candidate(question_id: int, difficulty: int = 1, points: list[str] | None = None,
              tags: list[str] | None = None) -> Candidate:
    return Candidate(
        id=question_id,
        type="DIALOGUE",
        content=f"topic {question_id}",
        difficulty=difficulty,
        assessment_points=points or [],
        tags=tags or [],
    )


def engine_context(candidates, used=(), **overrides) -> EngineContext:
    return EngineContext(
        candidates=list(candidates),
        used_question_ids=frozenset(used),
        dimensions=tuple(overrides.get("dimensions", ())),
        assessment_points=tuple(overrides.get("points", ())),
        current_question=overrides.get("current"),
        current_question_finished=overrides.get("current_finished", True),
        question_count=overrides.get("question_count", 0),
        completed_count=overrides.get("completed_count", 0),
    )


def dialogue_request(turn_count: int = 0, **overrides) -> DialogueRequest:
    return DialogueRequest(
        topic=overrides.get("topic", "提示词工程"),
        rubric=overrides.get("rubric", "必须说明目标、角色、约束和输出格式"),
        history=overrides.get("history", [Message(sender_type="student", content="我先说结论")]),
        assessment_points=overrides.get("assessment_points", ["结构化表达"]),
        topic_turn_count=turn_count,
    )


def dialogue_state(turn_count: int = 0, **overrides) -> dict:
    """对话图的初始状态（等于门面把 DialogueRequest 翻译过来的结果）。"""
    request = dialogue_request(turn_count, **overrides)
    return {
        "topic": request.topic,
        "rubric": request.rubric,
        "assessment_points": list(request.assessment_points),
        "history": list(request.history),
        "topic_history": list(overrides.get("topic_history") or request.history),
        "topic_turn_count": request.topic_turn_count,
        "attempts": 0,
    }
