"""Agent 的能力接口。

这一层是薄的：解析请求 → 交给 AssessmentAgent → 包装响应。
除了 SSE 的报文格式（这是 HTTP 传输的事），不应有别的逻辑。

注意：这不是测评的对外接口。测评过程走 /internal/v1/assessments/*，
由 app/assessment/flow.py 在进程内直接调用 Agent；出题引擎也只在那边用。

评分接口用的是流程层持有的那个评分工具（`flow.scoring_tool`），
所以这里返回的分数与真实测评里用的算法**必然一致**——换算法只要换工具，
这个接口跟着变，不会出现"接口一套算法、测评另一套"。
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.agent import AssessmentAgent
from app.api.dependencies import get_agent, get_flow, require_service_token
from app.assessment import AssessmentFlow
from app.core.exceptions import AgentNotConfigured
from app.domain.schemas import DialogueRequest, ScoreRequest

router = APIRouter(prefix="/internal/v1/agent", tags=["agent"], dependencies=[Depends(require_service_token)])


@router.post("/dialogue")
async def dialogue(request: DialogueRequest, agent: AssessmentAgent = Depends(get_agent)):
    try:
        return await agent.reply(request)
    except AgentNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"model dialogue failed: {exc}") from exc


@router.post("/dialogue/stream")
async def dialogue_stream(request: DialogueRequest, agent: AssessmentAgent = Depends(get_agent)):
    async def events():
        try:
            async for kind, payload in agent.stream(request):
                if kind == "done":
                    # 序列化只在这里做：门面交出来的是对象，传输格式是这一层的事
                    yield f"event: done\ndata: {payload.model_dump_json()}\n\n"
                else:
                    yield f"event: delta\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except AgentNotConfigured as exc:
            yield f"event: error\ndata: {json.dumps(str(exc), ensure_ascii=False)}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps(f'model dialogue failed: {exc}', ensure_ascii=False)}\n\n"
    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/score")
async def score(request: ScoreRequest, flow: AssessmentFlow = Depends(get_flow)):
    try:
        return await flow.scoring_tool.score(request)
    except AgentNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"model scoring failed: {exc}") from exc
