from app.core.exceptions import NotFoundException
from app.utils.supabase_client import get_supabase

PIPELINE_SELECT = "id, name, description, active, display_order, created_at"
STAGE_SELECT = "id, pipeline_id, name, color, position, is_inicial, created_at"


async def list_pipelines(
    empresa_id: str, include_stages: bool = False
) -> list[dict]:
    """Lista pipelines ativos da empresa."""
    supabase = get_supabase()

    select = PIPELINE_SELECT
    if include_stages:
        select += f", stages({STAGE_SELECT})"

    result = (
        supabase.table("pipelines")
        .select(select)
        .eq("empresa_id", empresa_id)
        .eq("active", True)
        .order("display_order")
        .execute()
    )

    pipelines = result.data or []

    # Ordenar stages por position se incluídos
    if include_stages:
        for pipeline in pipelines:
            if pipeline.get("stages"):
                pipeline["stages"].sort(key=lambda s: s.get("position", 0))

    return pipelines


async def get_pipeline(empresa_id: str, pipeline_id: str) -> dict:
    """Busca um pipeline por ID com seus stages."""
    supabase = get_supabase()

    result = (
        supabase.table("pipelines")
        .select(f"{PIPELINE_SELECT}, stages({STAGE_SELECT})")
        .eq("id", pipeline_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise NotFoundException(f"Pipeline '{pipeline_id}' não encontrado")

    pipeline = result.data[0]

    # Ordenar stages por position
    if pipeline.get("stages"):
        pipeline["stages"].sort(key=lambda s: s.get("position", 0))

    return pipeline


async def list_stages(empresa_id: str, pipeline_id: str) -> list[dict]:
    """Lista stages de um pipeline específico."""
    supabase = get_supabase()

    # Validar que o pipeline pertence à empresa
    pipeline = (
        supabase.table("pipelines")
        .select("id")
        .eq("id", pipeline_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not pipeline.data:
        raise NotFoundException(f"Pipeline '{pipeline_id}' não encontrado")

    result = (
        supabase.table("stages")
        .select(STAGE_SELECT)
        .eq("pipeline_id", pipeline_id)
        .order("position")
        .execute()
    )

    return result.data or []
