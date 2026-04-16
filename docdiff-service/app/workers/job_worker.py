import logging

from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings
from app.pipeline.orchestrator import run_pipeline

logger = logging.getLogger("docdiff.worker")


async def process_comparison_job(ctx: dict, job_id: str) -> None:
    logger.info(f"Worker picked up job {job_id}")
    await run_pipeline(job_id)
    logger.info(f"Worker finished job {job_id}")


class WorkerSettings:
    functions = [process_comparison_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 1
    job_timeout = 600


async def enqueue_job(job_id: str) -> None:
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("process_comparison_job", job_id)
    await redis.close()
