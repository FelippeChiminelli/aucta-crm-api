from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# =====================================================
# Response Models
# =====================================================


class LeadPipelineInfo(BaseModel):
    """Info resumida do pipeline associado ao lead."""

    name: str


class LeadStageInfo(BaseModel):
    """Info resumida do stage associado ao lead."""

    name: str
    color: str | None = None


class LeadResponse(BaseModel):
    """Representação completa de um Lead na resposta da API."""

    id: str
    pipeline_id: str
    stage_id: str
    responsible_uuid: str | None = None
    name: str
    company: str | None = None
    value: float | None = None
    phone: str | None = None
    email: str | None = None
    origin: str | None = None
    status: str | None = None
    last_contact_at: str | None = None
    estimated_close_at: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    created_at: str
    # Campos de perda
    loss_reason_category: str | None = None
    loss_reason_notes: str | None = None
    lost_at: str | None = None
    # Campos de venda
    sold_at: str | None = None
    sold_value: float | None = None
    sale_notes: str | None = None
    # Relacionamentos
    pipeline: LeadPipelineInfo | None = None
    stage: LeadStageInfo | None = None


class LeadHistoryResponse(BaseModel):
    """Entrada do histórico de alterações de um lead."""

    id: str
    lead_id: str
    pipeline_id: str | None = None
    stage_id: str | None = None
    previous_pipeline_id: str | None = None
    previous_stage_id: str | None = None
    changed_at: str
    changed_by: str | None = None
    change_type: str
    notes: str | None = None
    created_at: str


# =====================================================
# Request Models
# =====================================================


class CreateLeadRequest(BaseModel):
    """Dados para criação de um novo lead."""

    pipeline_id: str = Field(..., description="ID do pipeline")
    stage_id: str = Field(..., description="ID do stage")
    name: str = Field(..., min_length=1, max_length=200, description="Nome do lead")
    company: str | None = Field(None, max_length=200, description="Empresa do lead")
    value: float | None = Field(None, ge=0, description="Valor estimado")
    phone: str | None = Field(None, max_length=20, description="Telefone")
    email: EmailStr | None = Field(None, description="E-mail")
    origin: str | None = Field(None, max_length=100, description="Origem do lead")
    status: str | None = Field("novo", description="Status do lead")
    tags: list[str] | None = Field(None, description="Tags do lead")
    notes: str | None = Field(None, description="Observações")
    responsible_uuid: str | None = Field(None, description="UUID do responsável")


class UpdateLeadRequest(BaseModel):
    """Dados para atualização parcial de um lead."""

    name: str | None = Field(None, min_length=1, max_length=200)
    company: str | None = Field(None, max_length=200)
    value: float | None = Field(None, ge=0)
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    origin: str | None = Field(None, max_length=100)
    status: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    responsible_uuid: str | None = None
    last_contact_at: str | None = None
    estimated_close_at: str | None = None


class MoveStageRequest(BaseModel):
    """Dados para mover um lead de stage."""

    stage_id: str = Field(..., description="ID do novo stage")
    notes: str | None = Field(None, description="Observações da mudança")


class MarkLostRequest(BaseModel):
    """Dados para marcar um lead como perdido."""

    loss_reason_category: str = Field(..., description="Categoria do motivo de perda")
    loss_reason_notes: str | None = Field(None, description="Notas adicionais")


class MarkSoldRequest(BaseModel):
    """Dados para marcar um lead como vendido."""

    sold_value: float = Field(..., ge=0, description="Valor final da venda")
    sale_notes: str | None = Field(None, description="Notas da venda")
    sold_at: str | None = Field(None, description="Data da venda (ISO)")


# =====================================================
# Filter Models
# =====================================================


class LeadFilters(BaseModel):
    """Filtros para listagem de leads."""

    search: str | None = None
    status: str | None = None
    pipeline_id: str | None = None
    stage_id: str | None = None
    responsible_uuid: str | None = None
    origin: str | None = None
    tags: list[str] | None = None
    created_from: str | None = None
    created_to: str | None = None
