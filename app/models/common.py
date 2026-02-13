from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Resposta paginada genérica."""

    data: list[T]
    total: int
    page: int
    limit: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Schema de resposta de erro."""

    detail: str


class SuccessResponse(BaseModel):
    """Schema de resposta de sucesso simples."""

    message: str
