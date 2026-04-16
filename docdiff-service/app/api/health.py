import logging
from fastapi import APIRouter
from sqlalchemy import text
from app.config import settings
from app.database import engine

logger = logging.getLogger("docdiff")
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    checks = {"service": "ok", "version": "0.1.0"}

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    if settings.qwen_local_endpoint:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.qwen_local_endpoint}/models")
                checks["qwen_local"] = "ok" if resp.status_code == 200 else f"status: {resp.status_code}"
        except Exception:
            checks["qwen_local"] = "unreachable"

    status = "ok" if all(v == "ok" for k, v in checks.items() if k not in ("qwen_local", "version")) else "degraded"
    checks["status"] = status
    return checks
