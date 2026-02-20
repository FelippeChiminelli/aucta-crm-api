from typing import Literal

from pydantic import BaseModel, Field


class CustomFieldResponse(BaseModel):
    """Definição de um campo customizado."""

    id: str
    pipeline_id: str | None = None
    name: str
    type: Literal["text", "number", "date", "select", "multiselect", "link", "vehicle", "product"]
    options: list[str] | None = None
    required: bool
    position: int
    created_at: str


class CustomValueResponse(BaseModel):
    """Valor de um campo customizado para um lead."""

    id: str
    lead_id: str
    field_id: str
    value: str


class SetCustomValueItem(BaseModel):
    """Item individual para setar um valor customizado."""

    field_id: str = Field(..., description="ID do campo customizado")
    value: str = Field(..., description="Valor do campo")


class SetCustomValuesRequest(BaseModel):
    """Request para setar múltiplos valores customizados de um lead."""

    values: list[SetCustomValueItem] = Field(
        ..., description="Lista de valores a setar"
    )
