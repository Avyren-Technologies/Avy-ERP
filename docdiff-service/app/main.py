import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.router import api_router
from app.config import settings

logger = logging.getLogger("docdiff")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=getattr(logging, settings.log_level))
    logger.info("DocDiff Pro starting up...")

    import os
    os.makedirs(f"{settings.storage_path}/uploads", exist_ok=True)
    os.makedirs(f"{settings.storage_path}/reports", exist_ok=True)

    from app.database import engine
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified")

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

app.include_router(health_router)
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
