from datetime import datetime, timezone

from app.core.exceptions import NotFoundException, ValidationException
from app.utils.pagination import build_paginated_response, paginate_query
from app.utils.supabase_client import get_supabase

# Campos selecionados para listagem (otimizado)
LEAD_SELECT_FIELDS = (
    "id, pipeline_id, stage_id, responsible_uuid, name, company, value, "
    "phone, email, origin, status, last_contact_at, estimated_close_at, "
    "tags, notes, created_at, loss_reason_category, loss_reason_notes, "
    "lost_at, sold_at, sold_value, sale_notes"
)

LEAD_SELECT_WITH_RELATIONS = (
    f"{LEAD_SELECT_FIELDS}, "
    "pipelines:pipeline_id(name), "
    "stages:stage_id(name, color)"
)


async def list_leads(
    empresa_id: str,
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    status: str | None = None,
    pipeline_id: str | None = None,
    stage_id: str | None = None,
    responsible_uuid: str | None = None,
    origin: str | None = None,
    tags: list[str] | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
) -> dict:
    """Lista leads paginados com filtros."""
    supabase = get_supabase()

    # Query base
    query = (
        supabase.table("leads")
        .select(LEAD_SELECT_WITH_RELATIONS, count="exact")
        .eq("empresa_id", empresa_id)
        .order("created_at", desc=True)
    )

    # Aplicar filtros
    query = _apply_lead_filters(
        query, search, status, pipeline_id, stage_id,
        responsible_uuid, origin, tags, created_from, created_to,
    )

    # Paginação
    query = paginate_query(query, page, limit)

    result = query.execute()
    total = result.count or 0
    data = _normalize_lead_relations(result.data or [])

    return build_paginated_response(data, total, page, limit)


async def get_lead(empresa_id: str, lead_id: str) -> dict:
    """Busca um lead por ID."""
    supabase = get_supabase()

    result = (
        supabase.table("leads")
        .select(LEAD_SELECT_WITH_RELATIONS)
        .eq("id", lead_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise NotFoundException(f"Lead '{lead_id}' não encontrado")

    return _normalize_lead_relations(result.data)[0]


async def create_lead(empresa_id: str, data: dict) -> dict:
    """Cria um novo lead."""
    supabase = get_supabase()

    # Validar pipeline e stage pertencem à empresa
    await _validate_pipeline_stage(empresa_id, data["pipeline_id"], data["stage_id"])

    # Formatar telefone brasileiro se necessário
    if data.get("phone"):
        data["phone"] = _format_brazilian_phone(data["phone"])

    lead_data = {**data, "empresa_id": empresa_id}

    result = (
        supabase.table("leads")
        .insert(lead_data)
        .execute()
    )

    if not result.data:
        raise ValidationException("Erro ao criar lead")

    return await get_lead(empresa_id, result.data[0]["id"])


async def update_lead(empresa_id: str, lead_id: str, data: dict) -> dict:
    """Atualiza parcialmente um lead."""
    supabase = get_supabase()

    # Verificar se lead existe
    await get_lead(empresa_id, lead_id)

    # Formatar telefone se enviado
    if data.get("phone"):
        data["phone"] = _format_brazilian_phone(data["phone"])

    # Remover campos None
    update_data = {k: v for k, v in data.items() if v is not None}

    if not update_data:
        return await get_lead(empresa_id, lead_id)

    supabase.table("leads").update(update_data).eq("id", lead_id).eq(
        "empresa_id", empresa_id
    ).execute()

    return await get_lead(empresa_id, lead_id)


async def delete_lead(empresa_id: str, lead_id: str) -> None:
    """Deleta um lead."""
    supabase = get_supabase()

    # Verificar se existe
    await get_lead(empresa_id, lead_id)

    supabase.table("leads").delete().eq("id", lead_id).eq(
        "empresa_id", empresa_id
    ).execute()


async def move_lead_stage(
    empresa_id: str, lead_id: str, new_stage_id: str, notes: str | None = None
) -> dict:
    """Move um lead para outro stage e cria histórico."""
    supabase = get_supabase()

    # Buscar lead atual
    current = await get_lead(empresa_id, lead_id)

    # Validar novo stage
    stage_result = (
        supabase.table("stages")
        .select("id, pipeline_id")
        .eq("id", new_stage_id)
        .execute()
    )

    if not stage_result.data:
        raise NotFoundException(f"Stage '{new_stage_id}' não encontrado")

    # Atualizar lead
    supabase.table("leads").update({"stage_id": new_stage_id}).eq("id", lead_id).eq(
        "empresa_id", empresa_id
    ).execute()

    # Criar histórico
    _create_history_entry(
        supabase,
        empresa_id=empresa_id,
        lead_id=lead_id,
        pipeline_id=current["pipeline_id"],
        stage_id=new_stage_id,
        previous_pipeline_id=current["pipeline_id"],
        previous_stage_id=current["stage_id"],
        change_type="stage_changed",
        notes=notes,
    )

    return await get_lead(empresa_id, lead_id)


async def mark_as_lost(
    empresa_id: str,
    lead_id: str,
    loss_reason_category: str,
    loss_reason_notes: str | None = None,
) -> dict:
    """Marca lead como perdido."""
    supabase = get_supabase()
    current = await get_lead(empresa_id, lead_id)
    now = datetime.now(timezone.utc).isoformat()

    supabase.table("leads").update(
        {
            "status": "perdido",
            "loss_reason_category": loss_reason_category,
            "loss_reason_notes": loss_reason_notes,
            "lost_at": now,
        }
    ).eq("id", lead_id).eq("empresa_id", empresa_id).execute()

    _create_history_entry(
        supabase,
        empresa_id=empresa_id,
        lead_id=lead_id,
        pipeline_id=current["pipeline_id"],
        stage_id=current["stage_id"],
        previous_pipeline_id=current["pipeline_id"],
        previous_stage_id=current["stage_id"],
        change_type="marked_as_lost",
        notes=loss_reason_notes,
    )

    return await get_lead(empresa_id, lead_id)


async def mark_as_sold(
    empresa_id: str,
    lead_id: str,
    sold_value: float,
    sale_notes: str | None = None,
    sold_at: str | None = None,
) -> dict:
    """Marca lead como vendido."""
    supabase = get_supabase()
    current = await get_lead(empresa_id, lead_id)
    now = sold_at or datetime.now(timezone.utc).isoformat()

    supabase.table("leads").update(
        {
            "status": "vendido",
            "sold_at": now,
            "sold_value": sold_value,
            "sale_notes": sale_notes,
        }
    ).eq("id", lead_id).eq("empresa_id", empresa_id).execute()

    _create_history_entry(
        supabase,
        empresa_id=empresa_id,
        lead_id=lead_id,
        pipeline_id=current["pipeline_id"],
        stage_id=current["stage_id"],
        previous_pipeline_id=current["pipeline_id"],
        previous_stage_id=current["stage_id"],
        change_type="marked_as_sold",
        notes=sale_notes,
    )

    return await get_lead(empresa_id, lead_id)


async def reactivate_lead(empresa_id: str, lead_id: str) -> dict:
    """Reativa um lead perdido ou vendido."""
    supabase = get_supabase()
    current = await get_lead(empresa_id, lead_id)

    supabase.table("leads").update(
        {
            "status": "morno",
            "loss_reason_category": None,
            "loss_reason_notes": None,
            "lost_at": None,
            "sold_at": None,
            "sold_value": None,
            "sale_notes": None,
        }
    ).eq("id", lead_id).eq("empresa_id", empresa_id).execute()

    _create_history_entry(
        supabase,
        empresa_id=empresa_id,
        lead_id=lead_id,
        pipeline_id=current["pipeline_id"],
        stage_id=current["stage_id"],
        previous_pipeline_id=current["pipeline_id"],
        previous_stage_id=current["stage_id"],
        change_type="reactivated",
        notes="Lead reativado via API",
    )

    return await get_lead(empresa_id, lead_id)


async def get_lead_history(empresa_id: str, lead_id: str) -> list[dict]:
    """Retorna o histórico de alterações de um lead."""
    supabase = get_supabase()

    # Verificar se lead existe
    await get_lead(empresa_id, lead_id)

    result = (
        supabase.table("lead_pipeline_history")
        .select("*")
        .eq("lead_id", lead_id)
        .eq("empresa_id", empresa_id)
        .order("changed_at", desc=True)
        .execute()
    )

    return result.data or []


async def get_all_tags(empresa_id: str) -> list[str]:
    """Retorna todas as tags únicas dos leads da empresa."""
    supabase = get_supabase()

    result = (
        supabase.table("leads")
        .select("tags")
        .eq("empresa_id", empresa_id)
        .not_.is_("tags", "null")
        .execute()
    )

    tags_set: set[str] = set()
    for row in result.data or []:
        if row.get("tags"):
            tags_set.update(row["tags"])

    return sorted(tags_set)


async def get_all_origins(empresa_id: str) -> list[str]:
    """Retorna todas as origens únicas dos leads da empresa."""
    supabase = get_supabase()

    result = (
        supabase.table("leads")
        .select("origin")
        .eq("empresa_id", empresa_id)
        .not_.is_("origin", "null")
        .execute()
    )

    origins = {row["origin"] for row in result.data or [] if row.get("origin")}
    return sorted(origins)


# =====================================================
# Funções auxiliares
# =====================================================


def _apply_lead_filters(
    query,
    search: str | None,
    status: str | None,
    pipeline_id: str | None,
    stage_id: str | None,
    responsible_uuid: str | None,
    origin: str | None,
    tags: list[str] | None,
    created_from: str | None,
    created_to: str | None,
):
    """Aplica filtros à query de leads."""
    if search:
        query = query.or_(
            f"name.ilike.%{search}%,"
            f"company.ilike.%{search}%,"
            f"email.ilike.%{search}%,"
            f"phone.ilike.%{search}%"
        )
    if status:
        query = query.eq("status", status)
    if pipeline_id:
        query = query.eq("pipeline_id", pipeline_id)
    if stage_id:
        query = query.eq("stage_id", stage_id)
    if responsible_uuid:
        query = query.eq("responsible_uuid", responsible_uuid)
    if origin:
        query = query.eq("origin", origin)
    if tags:
        query = query.contains("tags", tags)
    if created_from:
        query = query.gte("created_at", created_from)
    if created_to:
        query = query.lte("created_at", created_to)

    return query


async def _validate_pipeline_stage(
    empresa_id: str, pipeline_id: str, stage_id: str
) -> None:
    """Valida se pipeline e stage existem e pertencem à empresa."""
    supabase = get_supabase()

    pipeline = (
        supabase.table("pipelines")
        .select("id")
        .eq("id", pipeline_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not pipeline.data:
        raise ValidationException(f"Pipeline '{pipeline_id}' não encontrado")

    stage = (
        supabase.table("stages")
        .select("id")
        .eq("id", stage_id)
        .eq("pipeline_id", pipeline_id)
        .execute()
    )

    if not stage.data:
        raise ValidationException(
            f"Stage '{stage_id}' não encontrado no pipeline '{pipeline_id}'"
        )


def _normalize_lead_relations(leads: list[dict]) -> list[dict]:
    """Normaliza os nomes dos relacionamentos do Supabase para o formato da API."""
    for lead in leads:
        # Supabase retorna { pipelines: { name: "X" } } ao usar FK
        if "pipelines" in lead:
            lead["pipeline"] = lead.pop("pipelines")
        if "stages" in lead:
            lead["stage"] = lead.pop("stages")
    return leads


def _create_history_entry(supabase, **kwargs) -> None:
    """Cria uma entrada no histórico de pipeline do lead."""
    entry = {
        "changed_at": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }
    supabase.table("lead_pipeline_history").insert(entry).execute()


def _format_brazilian_phone(phone: str) -> str:
    """Formata número de telefone brasileiro removendo caracteres especiais."""
    cleaned = "".join(c for c in phone if c.isdigit())

    # Adiciona 55 se não começa com o código do país
    if len(cleaned) == 11:
        cleaned = f"55{cleaned}"
    elif len(cleaned) == 10:
        cleaned = f"55{cleaned}"

    return cleaned
