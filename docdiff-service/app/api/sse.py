import asyncio
import json
import uuid

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from jose import JWTError

from app.auth.jwt_validator import decode_jwt
from app.pipeline.orchestrator import get_job_progress

router = APIRouter(prefix="/jobs", tags=["sse"])


@router.get("/{job_id}/progress")
async def job_progress_sse(job_id: uuid.UUID, request: Request, token: str | None = Query(default=None)):
    """SSE endpoint. Auth via ?token=<jwt> query param (EventSource can't send headers)."""
    if token:
        try:
            decode_jwt(token)
        except JWTError:
            return JSONResponse(status_code=401, content={"error": "Invalid token"})
    async def event_stream():
        job_id_str = str(job_id)
        while True:
            if await request.is_disconnected():
                break
            progress = get_job_progress(job_id_str)
            if progress:
                yield f"data: {json.dumps(progress)}\n\n"
                if progress.get("status") in ("ready_for_review", "failed", "cancelled"):
                    break
            else:
                yield f"data: {json.dumps({'status': 'waiting', 'job_id': job_id_str})}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
