from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    meta: dict[str, int]


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str | None = None


class BBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    page: int
