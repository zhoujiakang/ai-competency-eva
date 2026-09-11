"""对话 Agent 门面：API 层唯一需要认识的对象。

它只做两件事：把请求翻译成图的状态，把图的最终状态翻译成响应。
真正的流程都在 app/agent/graphs.py 里，一眼能看完。

    对话  self.dialogue_graph  一次决策：追问，或者调用 next_question 结束本题

**评分不在这里。** 评分是一次「请求 → 结构化结果」的纯函数，没有节点之间的状态流转，
所以它不需要门面也不需要图，直接在 app/agent/scoring_tool.py 里完成。

边界（分两层，别混）：

  · **门面本身**不碰数据库、不鉴权、不写业务状态，只负责调用上面两张图；
  · **本服务整体**是直连 MySQL 的：出题（app/tools/question_selection.py）、
    写发题快照、写对话记忆、写评分结果都在 app/assessment/flow.py +
    app/db/repository.py 里完成。

权限的第一次校验在 Java 侧；这里只按 Java 传来的 X-User-Id 再校验一次测评归属
（AssessmentFlow._owned），不重复验登录态。
"""

import logging
from collections.abc import AsyncIterator

from app.agent.actions import ASK_FOLLOWUP
from app.agent.graphs import build_dialogue_graph
from app.agent.state import DialogueState
from app.core.config import Settings
from app.core.exceptions import ModelReplyError
from app.domain.schemas import DialogueRequest, DialogueResponse
from app.llm.client import LlmClient

logger = logging.getLogger("agent")


class AssessmentAgent:
    def __init__(
        self,
        settings: Settings,
        *,
        llm: LlmClient | None = None,
        dialogue_graph=None,
    ):
        self.settings = settings
        self.llm = llm or LlmClient(settings)
        # 依赖注入：单元测试或替换实现时，把任意一个传进来即可
        self.dialogue_graph = dialogue_graph or build_dialogue_graph(self.llm, settings)

    # ------------------------------------------------------------------ 对话
    @staticmethod
    def _dialogue_state(request: DialogueRequest) -> DialogueState:
        return {
            "topic": request.topic,
            "rubric": request.rubric,
            "assessment_points": list(request.assessment_points),
            "history": list(request.history),
            "topic_history": list(request.topic_history) or list(request.history),
            "topic_turn_count": request.topic_turn_count,
            "attempts": 0,
        }

    def _to_response(self, state: DialogueState | None) -> DialogueResponse:
        state = state or {}
        reply = state.get("reply") or ""
        if not reply:
            raise ModelReplyError(state.get("error") or "模型没有给出可用回复")
        return DialogueResponse(
            reply=reply,
            action=state.get("action") or ASK_FOLLOWUP,
            source=self.llm.source_name,
        )

    async def reply(self, request: DialogueRequest) -> DialogueResponse:
        """非流式：跑一遍对话图，拿最终状态。"""
        final = await self.dialogue_graph.ainvoke(self._dialogue_state(request))
        return self._to_response(final)

    async def stream(self, request: DialogueRequest) -> AsyncIterator[tuple[str, object]]:
        """流式：把图上节点的 custom 片段转成 delta，最后给一个 done。

        done 交出去的是 **DialogueResponse 对象**，不是 JSON 字符串——
        序列化是传输层的事（见 app/api/routes/agent.py），内部调用方（流程层）
        不需要为了拿一个字段先把它解析回来。
        """
        final: DialogueState | None = None
        async for mode, payload in self.dialogue_graph.astream(
            self._dialogue_state(request), stream_mode=["custom", "values"]
        ):
            if mode == "custom":
                yield "delta", payload["delta"]
            else:
                final = payload
        yield "done", self._to_response(final)
