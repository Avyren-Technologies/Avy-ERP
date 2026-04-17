import asyncio
import json
import uuid

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from jose import JWTError
from sqlalchemy import select

from app.auth.jwt_validator import decode_jwt
from app.database import async_session_factory
from app.models.job import ComparisonJob

router = APIRouter(prefix="/jobs", tags=["sse"])


@router.get("/{job_id}/progress")
async def job_progress_sse(
    job_id: uuid.UUID,
    request: Request,
    token: str | None = Query(default=None),
):
    """SSE endpoint that polls the DB directly so it works across
    the uvicorn / ARQ process boundary.
    Auth via ?token=<jwt> query param (EventSource can't send headers)."""
    if token:
        try:
            decode_jwt(token)
        except JWTError:
            return JSONResponse(status_code=401, content={"error": "Invalid token"})

    async def event_stream():
        job_id_str = str(job_id)
        terminal_statuses = {"ready_for_review", "failed", "cancelled", "completed"}

        while True:
            if await request.is_disconnected():
                break

            try:
                async with async_session_factory() as db:
                    result = await db.execute(
                        select(ComparisonJob).where(ComparisonJob.id == job_id)
                    )
                    job = result.scalar_one_or_none()

                    if job is None:
                        yield f"data: {json.dumps({'status': 'not_found', 'job_id': job_id_str})}\n\n"
                    else:
                        progress = {
                            "job_id": job_id_str,
                            "status": job.status.value,
                            "current_stage": job.current_stage or 0,
                            "stages": job.stage_progress or {},
                            "error": job.error_message,
                        }
                        yield f"data: {json.dumps(progress)}\n\n"
                        if job.status.value in terminal_statuses:
                            break
            except Exception as exc:
                yield f"data: {json.dumps({'status': 'error', 'error': str(exc)})}\n\n"

            await asyncio.sleep(2)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
