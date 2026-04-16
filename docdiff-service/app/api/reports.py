import os
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.config import settings
from app.models.difference import DetectedDifference
from app.models.document import Document, DocumentRole
from app.models.job import ComparisonJob
from app.models.report import DiffReport
from app.pdf.report_generator import generate_report_html, html_to_pdf
from app.schemas.common import SuccessResponse
from app.schemas.report import ReportResponse

router = APIRouter(prefix="/jobs", tags=["reports"])


def _difference_to_dict(d: DetectedDifference) -> dict:
    return {
        "difference_number": d.difference_number,
        "difference_type": d.difference_type.value if d.difference_type else "",
        "significance": d.significance.value if d.significance else "",
        "confidence": d.confidence,
        "page_version_a": d.page_version_a,
        "page_version_b": d.page_version_b,
        "value_before": d.value_before,
        "value_after": d.value_after,
        "summary": d.summary,
        "context": d.context,
        "verification_status": d.verification_status.value if d.verification_status else "pending",
        "verifier_comment": d.verifier_comment,
        "corrected_description": d.corrected_description,
        "needs_verification": d.needs_verification,
        "auto_confirmed": d.auto_confirmed,
    }


@router.post("/{job_id}/report", response_model=SuccessResponse[ReportResponse])
async def generate_report(
    job_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
):
    job_result = await db.execute(
        select(ComparisonJob)
        .options(selectinload(ComparisonJob.documents))
        .where(ComparisonJob.id == job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    # Load differences
    diff_result = await db.execute(
        select(DetectedDifference)
        .where(DetectedDifference.job_id == job_id)
        .order_by(DetectedDifference.difference_number)
    )
    differences = diff_result.scalars().all()

    # Build document labels map
    docs = {d.role: d for d in job.documents}
    doc_a = docs.get(DocumentRole.version_a)
    doc_b = docs.get(DocumentRole.version_b)
    documents_info = {
        "label_a": doc_a.label if doc_a else "Version A",
        "label_b": doc_b.label if doc_b else "Version B",
    }

    # Determine if partial (not all verified)
    total = job.total_differences or 0
    verified = job.differences_verified or 0
    is_partial = total > 0 and verified < total

    job_data = {
        "model_provider": job.model_provider,
        "model_name": job.model_name,
        "processing_time_ms": job.processing_time_ms,
        "is_partial": is_partial,
    }

    # Build summary stats
    summary_stats = {
        "total_differences": total,
        "material": sum(1 for d in differences if d.significance and d.significance.value == "material"),
        "substantive": sum(1 for d in differences if d.significance and d.significance.value == "substantive"),
        "cosmetic": sum(1 for d in differences if d.significance and d.significance.value == "cosmetic"),
        "confirmed": sum(1 for d in differences if d.verification_status and d.verification_status.value == "confirmed"),
        "dismissed": sum(1 for d in differences if d.verification_status and d.verification_status.value == "dismissed"),
        "flagged": sum(1 for d in differences if d.verification_status and d.verification_status.value == "flagged"),
        "corrected": sum(1 for d in differences if d.verification_status and d.verification_status.value == "corrected"),
        "pending": sum(1 for d in differences if d.verification_status and d.verification_status.value == "pending"),
        "differences_verified": verified,
        "is_partial": is_partial,
    }

    html = generate_report_html(
        job_data=job_data,
        differences=[_difference_to_dict(d) for d in differences],
        documents=documents_info,
    )

    # Upsert report
    existing_result = await db.execute(
        select(DiffReport).where(DiffReport.job_id == job_id)
    )
    report = existing_result.scalar_one_or_none()

    if report:
        report.report_html = html
        report.summary_stats = summary_stats
        report.is_partial = is_partial
        report.report_pdf_path = None  # Invalidate cached PDF
    else:
        report = DiffReport(
            job_id=job_id,
            report_html=html,
            summary_stats=summary_stats,
            is_partial=is_partial,
        )
        db.add(report)

    await db.commit()
    await db.refresh(report)

    return SuccessResponse(
        data=ReportResponse.model_validate(report),
        message="Report generated",
    )


@router.get("/{job_id}/report", response_model=SuccessResponse[ReportResponse])
async def get_report(
    job_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
):
    report_result = await db.execute(
        select(DiffReport).where(DiffReport.job_id == job_id)
    )
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found — generate it first via POST /jobs/{job_id}/report")

    return SuccessResponse(data=ReportResponse.model_validate(report))


@router.get("/{job_id}/report/pdf")
async def download_report_pdf(
    job_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
):
    report_result = await db.execute(
        select(DiffReport).where(DiffReport.job_id == job_id)
    )
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found — generate it first via POST /jobs/{job_id}/report")
    if not report.report_html:
        raise HTTPException(400, "Report HTML is empty — regenerate the report")

    # Generate PDF if not already cached
    if not report.report_pdf_path or not os.path.exists(report.report_pdf_path):
        pdf_dir = os.path.join(settings.storage_path, "reports")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"report_{job_id}.pdf")
        html_to_pdf(report.report_html, pdf_path)
        report.report_pdf_path = pdf_path
        await db.commit()

    return FileResponse(
        path=report.report_pdf_path,
        media_type="application/pdf",
        filename=f"docdiff_report_{job_id}.pdf",
    )
