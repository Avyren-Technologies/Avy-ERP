import asyncio
import json
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.pipeline.orchestrator import get_job_progress

router = APIRouter(prefix="/jobs", tags=["sse"])


@router.get("/{job_id}/progress")
async def job_progress_sse(job_id: uuid.UUID, request: Request):
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
