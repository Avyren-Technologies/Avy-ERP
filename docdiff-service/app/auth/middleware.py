from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import APIKeyUser, validate_api_key
from app.auth.jwt_validator import JWTUser, decode_jwt
from app.database import get_db


@dataclass
class AuthContext:
    user_id: str | None = None
    email: str | None = None
    company_id: str | None = None
    tenant_id: str | None = None
    api_key_id: str | None = None
    auth_method: str = "jwt"


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            jwt_user = decode_jwt(token)
            return AuthContext(
                user_id=jwt_user.user_id,
                email=jwt_user.email,
                company_id=jwt_user.company_id,
                tenant_id=jwt_user.tenant_id,
                auth_method="jwt",
            )
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired JWT token")

    api_key = request.headers.get("X-API-Key")
    if api_key:
        api_key_user = await validate_api_key(api_key, db)
        if api_key_user is None:
            raise HTTPException(status_code=401, detail="Invalid or revoked API key")
        return AuthContext(
            api_key_id=api_key_user.api_key_id,
            auth_method="api_key",
        )

    raise HTTPException(
        status_code=401,
        detail="Authentication required: provide Bearer token or X-API-Key header",
    )


CurrentUser = Annotated[AuthContext, Depends(get_current_user)]
