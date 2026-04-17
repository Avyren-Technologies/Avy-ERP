from fastapi import APIRouter

from app.api.api_keys import router as api_keys_router
from app.api.differences import router as differences_router
from app.api.documents import router as documents_router
from app.api.jobs import router as jobs_router
from app.api.reports import router as reports_router
from app.api.sse import router as sse_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(jobs_router)
api_router.include_router(sse_router)
api_router.include_router(differences_router)
api_router.include_router(documents_router)
api_router.include_router(reports_router)
api_router.include_router(api_keys_router)
