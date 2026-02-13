from fastapi import APIRouter, Query

from app.core.dependencies import EmpresaId
from app.models.pipeline import PipelineResponse, StageResponse
from app.services import pipeline_service

router = APIRouter()


@router.get("/pipelines", response_model=list[PipelineResponse])
async def list_pipelines(
    empresa_id: EmpresaId,
    include_stages: bool = Query(
        False, description="Incluir stages em cada pipeline"
    ),
):
    """
    Lista todos os pipelines ativos da empresa.

    Use `include_stages=true` para trazer os stages junto com cada pipeline.
    """
    return await pipeline_service.list_pipelines(empresa_id, include_stages)


@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: str, empresa_id: EmpresaId):
    """Busca um pipeline por ID, incluindo seus stages."""
    return await pipeline_service.get_pipeline(empresa_id, pipeline_id)


@router.get(
    "/pipelines/{pipeline_id}/stages", response_model=list[StageResponse]
)
async def list_stages(pipeline_id: str, empresa_id: EmpresaId):
    """Lista todos os stages de um pipeline, ordenados por posição."""
    return await pipeline_service.list_stages(empresa_id, pipeline_id)
