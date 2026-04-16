import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logger = logging.getLogger("docdiff")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=getattr(logging, settings.log_level))
    logger.info("DocDiff Pro starting up...")

    import os
    os.makedirs(f"{settings.storage_path}/uploads", exist_ok=True)
    os.makedirs(f"{settings.storage_path}/reports", exist_ok=True)

    yield

    logger.info("DocDiff Pro shutting down...")


app = FastAPI(
    title="DocDiff Pro",
    description="AI-powered document comparison and diff reporting service",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "docdiff-pro", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
