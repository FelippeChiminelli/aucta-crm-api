from fastapi import APIRouter, Query

from app.core.dependencies import EmpresaId
from app.models.custom_field import (
    CustomFieldResponse,
    CustomValueResponse,
    SetCustomValuesRequest,
)
from app.services import custom_field_service

router = APIRouter()


@router.get("/custom-fields", response_model=list[CustomFieldResponse])
async def list_custom_fields(
    empresa_id: EmpresaId,
    pipeline_id: str | None = Query(
        None,
        description="ID do pipeline para incluir campos específicos (além dos globais)",
    ),
):
    """
    Lista definições de campos customizados.

    Sem `pipeline_id`: retorna apenas campos globais.
    Com `pipeline_id`: retorna campos globais + específicos do pipeline.
    """
    return await custom_field_service.list_custom_fields(empresa_id, pipeline_id)


@router.get(
    "/leads/{lead_id}/custom-values",
    response_model=list[CustomValueResponse],
)
async def get_lead_custom_values(lead_id: str, empresa_id: EmpresaId):
    """Retorna os valores dos campos customizados de um lead."""
    return await custom_field_service.get_lead_custom_values(empresa_id, lead_id)


@router.put(
    "/leads/{lead_id}/custom-values",
    response_model=list[CustomValueResponse],
)
async def set_lead_custom_values(
    lead_id: str,
    data: SetCustomValuesRequest,
    empresa_id: EmpresaId,
):
    """
    Define valores de campos customizados para um lead.

    Atualiza valores existentes ou cria novos conforme necessário.
    """
    values = [item.model_dump() for item in data.values]
    return await custom_field_service.set_lead_custom_values(
        empresa_id, lead_id, values
    )
