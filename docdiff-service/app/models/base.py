from sqlalchemy.orm import DeclarativeBase

from app.config import settings

SCHEMA = settings.database_schema


class Base(DeclarativeBase):
    __table_args__ = {"schema": SCHEMA}
