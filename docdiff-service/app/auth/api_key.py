import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey


@dataclass
class APIKeyUser:
    api_key_id: str
    name: str


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    return f"dd_{secrets.token_urlsafe(32)}"


async def validate_api_key(key: str, db: AsyncSession) -> APIKeyUser | None:
    key_hash = hash_api_key(key)
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        return None
    await db.execute(
        update(APIKey).where(APIKey.id == api_key.id).values(last_used_at=datetime.now(tz=timezone.utc))
    )
    await db.commit()
    return APIKeyUser(api_key_id=str(api_key.id), name=api_key.name)
