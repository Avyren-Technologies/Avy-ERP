from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import AuthContext, get_current_user
from app.database import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[AuthContext, Depends(get_current_user)]
