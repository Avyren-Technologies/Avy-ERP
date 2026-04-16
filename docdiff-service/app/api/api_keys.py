import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.auth.api_key import generate_api_key, hash_api_key
from app.models.api_key import APIKey
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class APIKeyCreateRequest(BaseModel):
    name: str


class APIKeyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None


class APIKeyCreateResponse(BaseModel):
    id: uuid.UUID
    name: str
    key: str  # Returned only once at creation
    is_active: bool
    created_at: datetime


@router.post("", response_model=SuccessResponse[APIKeyCreateResponse], status_code=201)
async def create_api_key(
    body: APIKeyCreateRequest,
    db: DbSession,
    user: CurrentUser,
):
    # JWT auth required to manage API keys
    if user.auth_method != "jwt":
        raise HTTPException(403, "JWT authentication required to manage API keys")

    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)

    api_key = APIKey(
        key_hash=key_hash,
        name=body.name,
        is_active=True,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return SuccessResponse(
        data=APIKeyCreateResponse(
            id=api_key.id,
            name=api_key.name,
            key=raw_key,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
        ),
        message="API key created — store the key securely, it will not be shown again",
    )


@router.get("", response_model=SuccessResponse[list[APIKeyResponse]])
async def list_api_keys(
    db: DbSession,
    user: CurrentUser,
):
    if user.auth_method != "jwt":
        raise HTTPException(403, "JWT authentication required to manage API keys")

    result = await db.execute(
        select(APIKey).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return SuccessResponse(
        data=[APIKeyResponse.model_validate(k) for k in keys]
    )


@router.delete("/{key_id}", response_model=SuccessResponse[None])
async def revoke_api_key(
    key_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
):
    if user.auth_method != "jwt":
        raise HTTPException(403, "JWT authentication required to manage API keys")

    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(404, "API key not found")

    api_key.is_active = False
    await db.commit()

    return SuccessResponse(data=None, message="API key revoked")
