from fastapi import APIRouter, Query

from app.core.dependencies import EmpresaId
from app.models.common import PaginatedResponse, SuccessResponse
from app.models.lead import (
    CreateLeadRequest,
    LeadHistoryResponse,
    LeadResponse,
    MarkLostRequest,
    MarkSoldRequest,
    MoveStageRequest,
    UpdateLeadRequest,
)
from app.services import lead_service

router = APIRouter()


@router.get("/leads", response_model=PaginatedResponse[LeadResponse])
async def list_leads(
    empresa_id: EmpresaId,
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
    search: str | None = Query(None, description="Busca por nome, empresa, email ou telefone"),
    status: str | None = Query(None, description="Filtrar por status"),
    pipeline_id: str | None = Query(None, description="Filtrar por pipeline"),
    stage_id: str | None = Query(None, description="Filtrar por stage"),
    responsible_uuid: str | None = Query(None, description="Filtrar por responsável"),
    origin: str | None = Query(None, description="Filtrar por origem"),
    tags: list[str] | None = Query(None, description="Filtrar por tags"),
    created_from: str | None = Query(None, description="Data de criação inicial (ISO)"),
    created_to: str | None = Query(None, description="Data de criação final (ISO)"),
):
    """
    Lista leads da empresa com paginação e filtros.

    Suporta busca textual por nome, empresa, email e telefone.
    Filtragem por pipeline, stage, status, responsável, origem e tags.
    """
    return await lead_service.list_leads(
        empresa_id=empresa_id,
        page=page,
        limit=limit,
        search=search,
        status=status,
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        responsible_uuid=responsible_uuid,
        origin=origin,
        tags=tags,
        created_from=created_from,
        created_to=created_to,
    )


@router.get("/leads/tags", response_model=list[str])
async def list_tags(empresa_id: EmpresaId):
    """Retorna todas as tags únicas dos leads da empresa."""
    return await lead_service.get_all_tags(empresa_id)


@router.get("/leads/origins", response_model=list[str])
async def list_origins(empresa_id: EmpresaId):
    """Retorna todas as origens únicas dos leads da empresa."""
    return await lead_service.get_all_origins(empresa_id)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: str, empresa_id: EmpresaId):
    """Busca um lead por ID."""
    return await lead_service.get_lead(empresa_id, lead_id)


@router.post("/leads", response_model=LeadResponse, status_code=201)
async def create_lead(data: CreateLeadRequest, empresa_id: EmpresaId):
    """
    Cria um novo lead.

    Campos obrigatórios: `pipeline_id`, `stage_id`, `name`.
    O telefone brasileiro é formatado automaticamente.
    """
    return await lead_service.create_lead(
        empresa_id, data.model_dump(exclude_none=True)
    )


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str, data: UpdateLeadRequest, empresa_id: EmpresaId
):
    """Atualiza parcialmente um lead. Envie apenas os campos que deseja alterar."""
    return await lead_service.update_lead(
        empresa_id, lead_id, data.model_dump(exclude_none=True)
    )


@router.delete("/leads/{lead_id}", response_model=SuccessResponse)
async def delete_lead(lead_id: str, empresa_id: EmpresaId):
    """Deleta um lead permanentemente."""
    await lead_service.delete_lead(empresa_id, lead_id)
    return SuccessResponse(message="Lead deletado com sucesso")


@router.patch("/leads/{lead_id}/stage", response_model=LeadResponse)
async def move_stage(
    lead_id: str, data: MoveStageRequest, empresa_id: EmpresaId
):
    """
    Move um lead para outro stage.

    Cria automaticamente uma entrada no histórico do lead.
    """
    return await lead_service.move_lead_stage(
        empresa_id, lead_id, data.stage_id, data.notes
    )


@router.post("/leads/{lead_id}/mark-lost", response_model=LeadResponse)
async def mark_lost(
    lead_id: str, data: MarkLostRequest, empresa_id: EmpresaId
):
    """
    Marca um lead como perdido.

    Define o status como 'perdido' e registra o motivo de perda.
    """
    return await lead_service.mark_as_lost(
        empresa_id, lead_id, data.loss_reason_category, data.loss_reason_notes
    )


@router.post("/leads/{lead_id}/mark-sold", response_model=LeadResponse)
async def mark_sold(
    lead_id: str, data: MarkSoldRequest, empresa_id: EmpresaId
):
    """
    Marca um lead como vendido.

    Define o status como 'vendido' e registra o valor e notas da venda.
    """
    return await lead_service.mark_as_sold(
        empresa_id,
        lead_id,
        data.sold_value,
        data.sale_notes,
        data.sold_at,
    )


@router.post("/leads/{lead_id}/reactivate", response_model=LeadResponse)
async def reactivate_lead(lead_id: str, empresa_id: EmpresaId):
    """
    Reativa um lead perdido ou vendido.

    Limpa os campos de perda/venda e define o status como 'morno'.
    """
    return await lead_service.reactivate_lead(empresa_id, lead_id)


@router.get(
    "/leads/{lead_id}/history", response_model=list[LeadHistoryResponse]
)
async def get_lead_history(lead_id: str, empresa_id: EmpresaId):
    """Retorna o histórico de alterações de pipeline/stage de um lead."""
    return await lead_service.get_lead_history(empresa_id, lead_id)
