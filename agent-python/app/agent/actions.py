"""Agent 的动作：追问，或者结束当前主题。

一个回合只做一件事，模型用工具调用把它表达出来：

    ask_followup   继续围绕当前主题追问
    next_question  当前主题结束，系统进入下一题

模型必须调用其中一个（`tool_choice="required"`），所以两个动作在结构上互斥，
不可能既追问又换题。工具只是「决策的载体」：它不改任何状态，
真正的关题、评分、换下一题由 assessment/flow.py 在发言流完之后执行。

决策和发言是两次调用（见 dialogue.py）。如果把它们合成一次，就会出现两种事故，
两种都在真实运行里出现过：

    · 模型嘴上追问，系统却按自己的判断换了题；
    · 模型嘴上收尾、同时返回 next_question，决策被当成噪声丢掉，题目关不掉，学生卡住。
"""

from __future__ import annotations

ASK_FOLLOWUP = "ask_followup"
NEXT_QUESTION = "next_question"

_ASK_FOLLOWUP_TOOL = {
    "type": "function",
    "function": {
        "name": ASK_FOLLOWUP,
        "description": (
            "继续围绕当前主题追问。学生还在正常作答，但对依据、边界条件、验证方式等说得还不够时选它。"
            "拿不准就选它：多问一句比草率结束一个话题更可接受。"
        ),
        "parameters": {
            "type": "object",
            "properties": {"reason": {"type": "string", "description": "一句话说明为什么还要追问"}},
            "required": ["reason"],
        },
    },
}

_NEXT_QUESTION_TOOL = {
    "type": "function",
    "function": {
        "name": NEXT_QUESTION,
        "description": (
            "结束当前主题，让测评进入下一题。只有下面三种情况才选它："
            "① 学生对当前主题给出的证据已经覆盖评分关注点的主要维度；"
            "② 学生表示不会、不知道、答不上来；"
            "③ 学生要求跳过、下一题、换一题、不要这题，或让你直接给 0 分。"
        ),
        "parameters": {
            "type": "object",
            "properties": {"reason": {"type": "string", "description": "一句话说明为什么结束当前主题"}},
            "required": ["reason"],
        },
    },
}

TURN_TOOLS: list[dict] = [_ASK_FOLLOWUP_TOOL, _NEXT_QUESTION_TOOL]
