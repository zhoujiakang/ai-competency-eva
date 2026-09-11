"""模型客户端的纯函数部分（不发真实请求）。"""

from types import SimpleNamespace

import anyio
import pytest

from app.core.exceptions import ModelReplyError
from app.llm.client import LlmClient, extract_json, parse_arguments
from tests.support import settings


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('{"a": 1}', '{"a": 1}'),
        ('```json\n{"a": 1}\n```', '{"a": 1}'),
        ('好的，结果是：{"a": 1} 希望有帮助', '{"a": 1}'),
    ],
)
def test_extract_json_handles_wrappers(raw, expected):
    assert extract_json(raw) == expected


@pytest.mark.parametrize("raw", ["没有 JSON", "", "只有 } 半个"])
def test_extract_json_rejects_garbage(raw):
    with pytest.raises(ModelReplyError):
        extract_json(raw)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('{"reason": "够了"}', {"reason": "够了"}),
        ("", {}),
        ("{半个", {}),
        ("[1, 2]", {}),        # 不是对象也当空参数
    ],
)
def test_parse_arguments_never_raises(raw, expected):
    assert parse_arguments(raw) == expected


def _tool_call(id="call_1", name="next_question", arguments="{}"):
    return SimpleNamespace(id=id, function=SimpleNamespace(name=name, arguments=arguments))


def _response(content=None, tool_calls=None):
    """一个非流式的 chat completion 响应，只带 call_tool 会读到的字段。"""
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeCompletions:
    def __init__(self, response):
        self._response = response
        self.requests: list[dict] = []

    async def create(self, **payload):
        self.requests.append(payload)
        return self._response


def fake_client(response):
    llm = LlmClient(settings())
    completions = FakeCompletions(response)
    llm._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return llm, completions


def collect(llm, **kwargs):
    async def run():
        return await llm.call_tool(messages=[{"role": "user", "content": "hi"}], **kwargs)

    return anyio.run(run)


TOOLS = [{"type": "function", "function": {"name": "next_question", "parameters": {}}}]


def test_call_tool_returns_the_first_tool_call():
    llm, completions = fake_client(_response(tool_calls=[_tool_call(arguments='{"reason": "够了"}')]))

    call = collect(llm, tools=TOOLS)

    assert call == {
        "id": "call_1",
        "name": "next_question",
        "arguments_text": '{"reason": "够了"}',
        "arguments": {"reason": "够了"},
    }
    assert completions.requests[0]["tools"] == TOOLS
    assert completions.requests[0]["tool_choice"] == "required"


def test_call_tool_returns_none_when_the_model_calls_nothing():
    llm, _ = fake_client(_response(content="我觉得还是继续问吧。"))

    assert collect(llm, tools=TOOLS) is None


def test_call_tool_discards_any_prose_the_model_adds():
    """决策轮说的话不算数：正文一律不进 call_tool 的返回值。"""
    llm, _ = fake_client(_response(
        content="好，那这题我们就到这里。",
        tool_calls=[_tool_call()],
    ))

    call = collect(llm, tools=TOOLS)

    assert call["name"] == "next_question"
    assert "comment" not in call


def test_call_tool_falls_back_to_empty_arguments_on_broken_json():
    llm, _ = fake_client(_response(tool_calls=[_tool_call(arguments="{坏了")]))

    call = collect(llm, tools=TOOLS)

    assert call["name"] == "next_question"
    assert call["arguments"] == {}
