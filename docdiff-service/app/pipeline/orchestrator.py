import logging
import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.router import get_provider
from app.config import settings
from app.database import async_session_factory
from app.models.job import ComparisonJob, JobStatus
from app.pipeline.stage_1_ingestion import run_stage_1
from app.pipeline.stage_2_classification import run_stage_2
from app.pipeline.stage_3_extraction import run_stage_3
from app.pipeline.stage_4_normalization import run_stage_4
from app.pipeline.stage_5_alignment import run_stage_5
from app.pipeline.stage_6_diff import run_stage_6
from app.pipeline.stage_7_scoring import run_stage_7
from app.pipeline.stage_8_assembly import run_stage_8

logger = logging.getLogger("docdiff.pipeline")

# In-memory progress store for SSE
_job_progress: dict[str, dict] = {}


def get_job_progress(job_id: str) -> dict | None:
    return _job_progress.get(job_id)


STAGE_STATUS_MAP = {
    1: JobStatus.parsing_version_a,
    2: JobStatus.parsing_version_b,
    3: JobStatus.parsing_version_b,
    4: JobStatus.aligning,
    5: JobStatus.aligning,
    6: JobStatus.diffing,
    7: JobStatus.classifying,
    8: JobStatus.assembling,
}


async def run_pipeline(job_id: str) -> None:
    uid = uuid.UUID(job_id)
    start_time = time.time()

    progress: dict = {"job_id": job_id, "status": "processing", "current_stage": 0, "stages": {}}
    _job_progress[job_id] = progress

    async with async_session_factory() as db:
        try:
            result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == uid))
            job = result.scalar_one_or_none()
            if not job:
                return

            ai_provider = get_provider(job.model_provider, job.model_name)

            # Stages 1-4
            stage_fns = [
                (1, "Ingestion & Validation", lambda: run_stage_1(uid, db)),
                (2, "Page Classification", lambda: run_stage_2(uid, db)),
                (3, "Content Extraction", lambda: run_stage_3(uid, db, ai_provider)),
                (4, "Normalization", lambda: run_stage_4(uid, db)),
            ]

            for stage_num, stage_name, stage_fn in stage_fns:
                await db.refresh(job)
                if job.status == JobStatus.cancelled:
                    progress["status"] = "cancelled"
                    return

                _update_progress(progress, stage_num, "in_progress", stage_name)
                job.current_stage = stage_num
                job.status = STAGE_STATUS_MAP.get(stage_num, JobStatus.parsing_version_a)
                job.stage_progress = dict(progress["stages"])
                await db.commit()

                success = await stage_fn()
                if not success:
                    _update_progress(progress, stage_num, "failed", stage_name)
                    job.status = JobStatus.failed
                    await db.commit()
                    progress["status"] = "failed"
                    return
                _update_progress(progress, stage_num, "completed", stage_name)

            # Stage 5: Alignment
            _update_progress(progress, 5, "in_progress", "Section Alignment")
            job.current_stage = 5
            job.status = JobStatus.aligning
            await db.commit()
            aligned_pairs = await run_stage_5(uid, db)
            _update_progress(progress, 5, "completed", "Section Alignment")

            # Stage 6: Diff
            _update_progress(progress, 6, "in_progress", "Computing Differences")
            job.current_stage = 6
            job.status = JobStatus.diffing
            await db.commit()
            diff_records = run_stage_6(aligned_pairs)
            _update_progress(progress, 6, "completed", "Computing Differences")

            # Stage 7: Scoring
            _update_progress(progress, 7, "in_progress", "Classifying Differences")
            job.current_stage = 7
            job.status = JobStatus.classifying
            await db.commit()
            scored = await run_stage_7(
                diff_records, ai_provider, settings.confidence_threshold, job.auto_confirm_threshold
            )
            _update_progress(progress, 7, "completed", "Classifying Differences")

            # Stage 8: Assembly
            _update_progress(progress, 8, "in_progress", "Assembling Results")
            job.current_stage = 8
            job.status = JobStatus.assembling
            await db.commit()
            await run_stage_8(uid, scored, db)
            _update_progress(progress, 8, "completed", "Assembling Results")

            elapsed = int((time.time() - start_time) * 1000)
            await db.refresh(job)
            job.processing_time_ms = elapsed
            await db.commit()
            progress["status"] = "ready_for_review"

        except Exception as e:
            logger.exception(f"Pipeline failed for job {job_id}: {e}")
            try:
                result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == uid))
                job = result.scalar_one_or_none()
                if job:
                    job.status = JobStatus.failed
                    job.error_message = str(e)
                    await db.commit()
            except Exception:
                pass
            progress["status"] = "failed"
            progress["error"] = str(e)


def _update_progress(progress: dict, stage: int, status: str, name: str) -> None:
    progress["current_stage"] = stage
    progress["stages"][str(stage)] = {"status": status, "name": name}
