from app.core.exceptions import NotFoundException
from app.utils.supabase_client import get_supabase

FIELD_SELECT = "id, pipeline_id, name, type, options, required, position, created_at"
VALUE_SELECT = "id, lead_id, field_id, value"


async def list_custom_fields(
    empresa_id: str, pipeline_id: str | None = None
) -> list[dict]:
    """
    Lista campos customizados da empresa.

    Se pipeline_id é fornecido, retorna campos globais + do pipeline.
    Caso contrário, retorna apenas campos globais.
    """
    supabase = get_supabase()

    if pipeline_id:
        # Campos globais (pipeline_id IS NULL) + específicos do pipeline
        result = (
            supabase.table("lead_custom_fields")
            .select(FIELD_SELECT)
            .eq("empresa_id", empresa_id)
            .or_(f"pipeline_id.is.null,pipeline_id.eq.{pipeline_id}")
            .order("position")
            .execute()
        )
    else:
        # Apenas campos globais
        result = (
            supabase.table("lead_custom_fields")
            .select(FIELD_SELECT)
            .eq("empresa_id", empresa_id)
            .is_("pipeline_id", "null")
            .order("position")
            .execute()
        )

    return result.data or []


async def get_lead_custom_values(
    empresa_id: str, lead_id: str
) -> list[dict]:
    """Retorna os valores customizados de um lead."""
    supabase = get_supabase()

    # Verificar se o lead pertence à empresa
    lead = (
        supabase.table("leads")
        .select("id")
        .eq("id", lead_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not lead.data:
        raise NotFoundException(f"Lead '{lead_id}' não encontrado")

    result = (
        supabase.table("lead_custom_values")
        .select(VALUE_SELECT)
        .eq("lead_id", lead_id)
        .execute()
    )

    return result.data or []


async def set_lead_custom_values(
    empresa_id: str, lead_id: str, values: list[dict]
) -> list[dict]:
    """
    Define valores customizados de um lead.

    Para cada par (field_id, value):
    - Se já existe um valor para aquele campo, atualiza.
    - Se não existe, cria um novo.
    """
    supabase = get_supabase()

    # Verificar se o lead pertence à empresa
    lead = (
        supabase.table("leads")
        .select("id")
        .eq("id", lead_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not lead.data:
        raise NotFoundException(f"Lead '{lead_id}' não encontrado")

    # Buscar valores existentes
    existing = (
        supabase.table("lead_custom_values")
        .select("id, field_id")
        .eq("lead_id", lead_id)
        .execute()
    )

    existing_map = {row["field_id"]: row["id"] for row in existing.data or []}

    for item in values:
        field_id = item["field_id"]
        value = item["value"]

        if field_id in existing_map:
            # Atualizar existente
            supabase.table("lead_custom_values").update(
                {"value": value}
            ).eq("id", existing_map[field_id]).execute()
        else:
            # Criar novo
            supabase.table("lead_custom_values").insert(
                {"lead_id": lead_id, "field_id": field_id, "value": value}
            ).execute()

    return await get_lead_custom_values(empresa_id, lead_id)
