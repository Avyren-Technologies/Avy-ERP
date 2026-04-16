from dataclasses import dataclass

from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"


@dataclass
class JWTUser:
    user_id: str
    email: str
    tenant_id: str | None = None
    company_id: str | None = None
    employee_id: str | None = None
    role_id: str | None = None


def decode_jwt(token: str) -> JWTUser:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    return JWTUser(
        user_id=payload["userId"],
        email=payload["email"],
        tenant_id=payload.get("tenantId"),
        company_id=payload.get("companyId"),
        employee_id=payload.get("employeeId"),
        role_id=payload.get("roleId"),
    )
