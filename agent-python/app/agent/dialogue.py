"""对话节点：一个回合 = 先决策，再发言。两件事分两次调用，这是这里唯一的设计要点。

    决策（静默，不流式）   模型必须调用 ask_followup 或 next_question 之一
        │
        ├─ ask_followup  → 用「追问」提示词生成发言 ──► 流式发给学生
        └─ next_question → 用「收尾」提示词生成发言 ──► 流式发给学生

**为什么非要拆成两次调用。** 合在一次里，「说什么」和「做什么」是同一次响应的两个独立产物，
可以互相矛盾，而且已经真的矛盾过两次：

    1. 模型嘴上追问，系统却按自己的判断换了题 —— 学生同时看到追问和新题；
    2. 模型嘴上收尾、同时返回 next_question，决策被当成噪声丢掉 —— 题目关不掉，学生卡住。

拆开之后不存在这个空间：动作先定下来，话再按动作、用对应的提示词生成。
说「追问」时那段提示词只让它追问，说「收尾」时只让它收尾。话和状态不可能不一致。

**流式不受影响。** 工具调用那一轮不流式、也不发给前端（前端此时显示「思考中」），
说给学生听的那句话仍然是逐字推出去的。用户看到的就是「先想，再说话」。

另外两条兜底：

  · 确定性规则（学生明确要跳过 / 轮次到顶）命中时不问模型，直接走收尾；
  · 决策失败（网络异常、模型没调工具）一律按「继续追问」处理——宁多问一句，
    也不草率结束一个话题，更不会把学生卡在一条没有下文的话题里。

流式的 JSON 包裹防护（GUARD_CHARS / looks_like_json）保留自旧实现：模型偶尔会把回复
包成 {"reply": "..."} 或 json 代码块，一旦转发学生就会看到 JSON。所以先攒够一小段，
确认不像 JSON 再开始往外发；确认像 JSON 就整段丢弃并重试——此时浏览器还没收到任何内容。
"""

import logging
import time

from app.agent.actions import ASK_FOLLOWUP, NEXT_QUESTION, TURN_TOOLS
from app.agent.completion import forced_action
from app.agent.prompts import CLOSING_SYSTEM, DECISION_SYSTEM, DIALOGUE_SYSTEM, TURN_USER
from app.agent.state import DialogueState
from app.agent.streaming import emit
from app.agent.transcript import render_history, render_points
from app.core.config import Settings
from app.llm.client import LlmClient

logger = logging.getLogger("agent.dialogue")

# 先攒够这么多字符再判断是不是 JSON 包裹
GUARD_CHARS = 12
# 发言最多重新生成几次
MAX_REPLY_ATTEMPTS = 2

# 发言一个字都生成不出来、但本题又必须结束时（例如学生要求跳过）的兜底收尾语。
# 保证学生至少看到一句收尾，而不是一个错误提示。
FALLBACK_CLOSING = "好，这题我们先过。"


def looks_like_json(text: str) -> bool:
    head = text.lstrip()[:40]
    return head.startswith("{") or head.startswith("```") or '"reply"' in head


def _user_text(state: DialogueState) -> str:
    """渲染用户输入；三段提示词共用同一段。"""
    return TURN_USER.substitute(
        topic=state.get("topic", ""),
        rubric=state.get("rubric", ""),
        points=render_points(state.get("assessment_points")),
        history=render_history(state.get("history", [])),
    )


async def _decide(llm: LlmClient, state: DialogueState) -> str:
    """决策轮：只取工具调用；模型顺带说的话一律丢弃，不发给学生。"""
    started = time.perf_counter()
    messages = [
        {"role": "system", "content": DECISION_SYSTEM.substitute()},
        {"role": "user", "content": _user_text(state)},
    ]
    try:
        call = await llm.call_tool(messages=messages, tools=TURN_TOOLS)
    except Exception as exc:  # 决策失败不报错：按"继续追问"处理，宁多问一句
        logger.warning("decision failed, keep asking topic=%s: %s", state.get("topic"), exc)
        return ASK_FOLLOWUP

    # 只认已知动作；模型抽风返回别的工具名时同样按"继续追问"处理
    action = call["name"] if call and call["name"] in (ASK_FOLLOWUP, NEXT_QUESTION) else ASK_FOLLOWUP
    logger.debug(
        "decision=%s (%s) topic=%s elapsed=%.2fs",
        action, (call or {}).get("arguments", {}).get("reason", ""), state.get("topic"),
        time.perf_counter() - started,
    )
    return action


async def _stream_reply(llm: LlmClient, system: str, user: str) -> tuple[str, bool]:
    """流式跑一次发言，返回 (正文, 是否已经说给学生听)。"""
    collected: list[str] = []
    emitted = False

    async for chunk in llm.stream(system=system, user=user):
        collected.append(chunk)
        if not emitted:
            # 还没确认安全，继续攒
            joined = "".join(collected)
            if len(joined) < GUARD_CHARS:
                continue
            if looks_like_json(joined):
                break
            emit(joined)
            emitted = True
        else:
            emit(chunk)

    text = "".join(collected).strip()
    if not emitted and text and not looks_like_json(text):
        # 回复很短（例如"好的。"），没触发安全检查，这里补发一次
        emit(text)
        emitted = True

    return text, emitted


async def _speak(llm: LlmClient, state: DialogueState, action: str) -> tuple[str, int, str]:
    """发言轮：按动作选提示词，把最终那句话流式发出去。"""
    system = (CLOSING_SYSTEM if action == NEXT_QUESTION else DIALOGUE_SYSTEM).substitute()
    user = _user_text(state)

    for attempt in range(1, MAX_REPLY_ATTEMPTS + 1):
        text, emitted = await _stream_reply(llm, system, user)
        if text and not looks_like_json(text):
            return text, attempt, ""
        logger.warning("reply unusable action=%s, retrying: %s", action, text[:40])
        if emitted:
            # 已经说给学生听了，收不回来，就把它当成这次发言
            return text, attempt, ""

    if action == NEXT_QUESTION:
        # 本题已经决定结束，不能因为一次输出失败把学生卡住
        emit(FALLBACK_CLOSING)
        return FALLBACK_CLOSING, MAX_REPLY_ATTEMPTS, ""

    return "", MAX_REPLY_ATTEMPTS, "模型输出不可用（空回复或被 JSON 包裹）"


def agent_turn_node(llm: LlmClient, settings: Settings):
    """一个回合：决策 → 发言。"""

    async def run(state: DialogueState) -> dict:
        started = time.perf_counter()

        # 保险零：确定性规则命中 → 本题必须结束，连决策轮都省掉
        topic_history = state.get("topic_history") or state.get("history", [])
        action = forced_action(topic_history, state.get("topic_turn_count", 0), settings.max_topic_turns)
        if action is None:
            action = await _decide(llm, state)
        else:
            logger.debug("deterministic rule forces %s topic=%s", action, state.get("topic"))

        reply, attempts, error = await _speak(llm, state, action)
        logger.debug(
            "turn done topic=%s action=%s attempts=%d chars=%d elapsed=%.2fs",
            state.get("topic"), action, attempts, len(reply), time.perf_counter() - started,
        )
        return {"reply": reply, "action": action, "attempts": attempts, "error": error}

    return run
