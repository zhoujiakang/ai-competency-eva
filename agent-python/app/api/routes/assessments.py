"""测评过程的对外接口。

这些接口由 Java 在鉴权后转发过来，前端不直接访问：

    GET  /{id}/conversation   恢复现场：整场对话 + 当前题目
    POST /{id}/chat/stream    对话（SSE）：题目 / 发言片段 / 某题问完 / 整场结束
    POST /{id}/complete       确认结束测评
    GET  /{id}/result         获取结果

身份来自 Java 塞进来的 X-User-Id 头，这里不重复验登录态。
"""

import json
import logging

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_flow, require_service_token
from app.assessment import AssessmentFlow

logger = logging.getLogger("agent.assessment")

router = APIRouter(prefix="/internal/v1/assessments", tags=["assessments"],
                   dependencies=[Depends(require_service_token)])


@router.get("/{assessment_id}/conversation")
async def conversation(assessment_id: int, x_user_id: int = Header(), flow: AssessmentFlow = Depends(get_flow)):
    try:
        return await flow.conversation(assessment_id, x_user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/{assessment_id}/chat/stream")
async def chat_stream(
    assessment_id: int,
    body: dict = Body(default_factory=dict),
    x_user_id: int = Header(),
    flow: AssessmentFlow = Depends(get_flow),
):
    """带内容表示学生的一次回答；不带内容表示"开场或继续"。"""
    content = (body or {}).get("content") or ""

    async def events():
        try:
            async for kind, payload in flow.chat(assessment_id, x_user_id, content):
                yield _sse(kind, payload)
        except (LookupError, PermissionError) as exc:
            yield _sse("error", {"message": str(exc)})
        except Exception as exc:  # 流已经开始，只能用事件报告失败
            logger.exception("chat failed assessment=%s", assessment_id)
            yield _sse("error", {"message": f"测评对话失败：{exc}"})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{assessment_id}/complete")
async def complete(assessment_id: int, x_user_id: int = Header(), flow: AssessmentFlow = Depends(get_flow)):
    try:
        return await flow.complete(assessment_id, x_user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/{assessment_id}/result")
async def result(assessment_id: int, x_user_id: int = Header(), flow: AssessmentFlow = Depends(get_flow)):
    try:
        return await flow.result(assessment_id, x_user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
