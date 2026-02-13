from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.utils.pagination import build_paginated_response, paginate_query
from app.utils.supabase_client import get_supabase

TASK_SELECT = (
    "id, title, description, empresa_id, assigned_to, created_by, "
    "lead_id, pipeline_id, task_type_id, status, priority, "
    "due_date, due_time, completed_at, started_at, tags, "
    "estimated_hours, actual_hours, created_at, updated_at, "
    "task_types(id, name, color, icon, active)"
)

COMMENT_SELECT = "id, task_id, user_id, comment, type, metadata, created_at"


# =====================================================
# Tasks CRUD
# =====================================================


async def list_tasks(
    empresa_id: str,
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    lead_id: str | None = None,
    pipeline_id: str | None = None,
    task_type_id: str | None = None,
) -> dict:
    """Lista tarefas da empresa com paginação e filtros."""
    supabase = get_supabase()

    # Query base
    query = (
        supabase.table("tasks")
        .select(TASK_SELECT, count="exact")
        .eq("empresa_id", empresa_id)
    )

    # Aplicar filtros
    if status:
        query = query.eq("status", status)
    if priority:
        query = query.eq("priority", priority)
    if assigned_to:
        query = query.eq("assigned_to", assigned_to)
    if lead_id:
        query = query.eq("lead_id", lead_id)
    if pipeline_id:
        query = query.eq("pipeline_id", pipeline_id)
    if task_type_id:
        query = query.eq("task_type_id", task_type_id)

    # Ordenação e paginação
    query = query.order("due_date", desc=False, nullsfirst=False)
    query = paginate_query(query, page, limit)

    result = query.execute()

    return build_paginated_response(
        data=result.data or [],
        total=result.count or 0,
        page=page,
        limit=limit,
    )


async def get_task(empresa_id: str, task_id: str) -> dict:
    """Busca uma tarefa por ID."""
    supabase = get_supabase()

    result = (
        supabase.table("tasks")
        .select(TASK_SELECT)
        .eq("id", task_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise NotFoundException(f"Tarefa '{task_id}' não encontrada")

    return result.data[0]


async def create_task(empresa_id: str, data: dict) -> dict:
    """Cria uma nova tarefa."""
    supabase = get_supabase()

    data["empresa_id"] = empresa_id

    result = (
        supabase.table("tasks")
        .insert(data)
        .execute()
    )

    # Buscar com relacionamentos
    return await get_task(empresa_id, result.data[0]["id"])


async def update_task(empresa_id: str, task_id: str, data: dict) -> dict:
    """Atualiza parcialmente uma tarefa."""
    supabase = get_supabase()

    # Validar que a tarefa pertence à empresa
    await get_task(empresa_id, task_id)

    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    supabase.table("tasks").update(data).eq("id", task_id).execute()

    return await get_task(empresa_id, task_id)


async def delete_task(empresa_id: str, task_id: str) -> None:
    """Deleta uma tarefa permanentemente."""
    supabase = get_supabase()

    # Validar que a tarefa pertence à empresa
    await get_task(empresa_id, task_id)

    supabase.table("tasks").delete().eq("id", task_id).execute()


# =====================================================
# Status transitions
# =====================================================


async def complete_task(empresa_id: str, task_id: str) -> dict:
    """Marca uma tarefa como concluída."""
    supabase = get_supabase()

    await get_task(empresa_id, task_id)

    now = datetime.now(timezone.utc).isoformat()
    supabase.table("tasks").update({
        "status": "concluida",
        "completed_at": now,
        "updated_at": now,
    }).eq("id", task_id).execute()

    return await get_task(empresa_id, task_id)


async def reopen_task(empresa_id: str, task_id: str) -> dict:
    """Reabre uma tarefa concluída."""
    supabase = get_supabase()

    await get_task(empresa_id, task_id)

    now = datetime.now(timezone.utc).isoformat()
    supabase.table("tasks").update({
        "status": "pendente",
        "completed_at": None,
        "updated_at": now,
    }).eq("id", task_id).execute()

    return await get_task(empresa_id, task_id)


# =====================================================
# Comments
# =====================================================


async def list_comments(empresa_id: str, task_id: str) -> list[dict]:
    """Lista comentários de uma tarefa."""
    supabase = get_supabase()

    # Validar que a tarefa pertence à empresa
    await get_task(empresa_id, task_id)

    result = (
        supabase.table("task_comments")
        .select(COMMENT_SELECT)
        .eq("task_id", task_id)
        .order("created_at", desc=False)
        .execute()
    )

    return result.data or []


async def create_comment(empresa_id: str, task_id: str, data: dict) -> dict:
    """Adiciona um comentário a uma tarefa."""
    supabase = get_supabase()

    # Validar que a tarefa pertence à empresa
    await get_task(empresa_id, task_id)

    data["task_id"] = task_id

    result = (
        supabase.table("task_comments")
        .insert(data)
        .execute()
    )

    return result.data[0]


# =====================================================
# Task Types
# =====================================================


async def list_task_types(empresa_id: str) -> list[dict]:
    """Lista tipos de tarefa da empresa."""
    supabase = get_supabase()

    result = (
        supabase.table("task_types")
        .select("id, name, color, icon, active")
        .eq("empresa_id", empresa_id)
        .eq("active", True)
        .order("name")
        .execute()
    )

    return result.data or []
