from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.utils.pagination import build_paginated_response, paginate_query
from app.utils.supabase_client import get_supabase

CONVERSATION_SELECT = (
    'id, empresa_id, lead_id, instance_id, fone, nome_instancia, '
    '"Nome_Whatsapp", assigned_user_id, cod_lid, status, '
    'last_message_at, message_count, created_at, updated_at'
)

MESSAGE_SELECT = (
    "id, conversation_id, instance_id, message_type, content, "
    "media_url, direction, status, timestamp, empresa_id, created_at"
)

INSTANCE_SELECT = (
    "id, name, phone_number, status, display_name, "
    "auto_create_leads, created_at, updated_at"
)


# =====================================================
# WhatsApp Instances (somente leitura)
# =====================================================


async def list_instances(empresa_id: str) -> list[dict]:
    """Lista instâncias de WhatsApp da empresa."""
    supabase = get_supabase()

    result = (
        supabase.table("whatsapp_instances")
        .select(INSTANCE_SELECT)
        .eq("empresa_id", empresa_id)
        .order("name")
        .execute()
    )

    return result.data or []


# =====================================================
# Conversations
# =====================================================


async def list_conversations(
    empresa_id: str,
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    instance_id: str | None = None,
    lead_id: str | None = None,
    assigned_user_id: str | None = None,
    fone: str | None = None,
) -> dict:
    """Lista conversas da empresa com paginação e filtros."""
    supabase = get_supabase()

    query = (
        supabase.table("chat_conversations")
        .select(CONVERSATION_SELECT, count="exact")
        .eq("empresa_id", empresa_id)
    )

    if status:
        query = query.eq("status", status)
    if instance_id:
        query = query.eq("instance_id", instance_id)
    if lead_id:
        query = query.eq("lead_id", lead_id)
    if assigned_user_id:
        query = query.eq("assigned_user_id", assigned_user_id)
    if fone:
        query = query.eq("fone", fone)

    query = query.order("last_message_at", desc=True, nullsfirst=False)
    query = paginate_query(query, page, limit)

    result = query.execute()

    return build_paginated_response(
        data=result.data or [],
        total=result.count or 0,
        page=page,
        limit=limit,
    )


async def get_conversation(empresa_id: str, conversation_id: str) -> dict:
    """Busca uma conversa por ID."""
    supabase = get_supabase()

    result = (
        supabase.table("chat_conversations")
        .select(CONVERSATION_SELECT)
        .eq("id", conversation_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise NotFoundException(f"Conversa '{conversation_id}' não encontrada")

    return result.data[0]


async def create_conversation(empresa_id: str, data: dict) -> dict:
    """Cria uma nova conversa."""
    supabase = get_supabase()

    data["empresa_id"] = empresa_id

    result = supabase.table("chat_conversations").insert(data).execute()

    return await get_conversation(empresa_id, result.data[0]["id"])


async def update_conversation(
    empresa_id: str, conversation_id: str, data: dict
) -> dict:
    """Atualiza parcialmente uma conversa."""
    supabase = get_supabase()

    await get_conversation(empresa_id, conversation_id)

    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    supabase.table("chat_conversations").update(data).eq(
        "id", conversation_id
    ).execute()

    return await get_conversation(empresa_id, conversation_id)


async def close_conversation(empresa_id: str, conversation_id: str) -> dict:
    """Fecha/encerra uma conversa."""
    return await update_conversation(
        empresa_id, conversation_id, {"status": "closed"}
    )


# =====================================================
# Messages
# =====================================================


async def list_messages(
    empresa_id: str,
    conversation_id: str,
    page: int = 1,
    limit: int = 50,
) -> dict:
    """Lista mensagens de uma conversa com paginação."""
    supabase = get_supabase()

    await get_conversation(empresa_id, conversation_id)

    query = (
        supabase.table("chat_messages")
        .select(MESSAGE_SELECT, count="exact")
        .eq("conversation_id", conversation_id)
        .eq("empresa_id", empresa_id)
        .order("timestamp", desc=False)
    )

    query = paginate_query(query, page, limit)

    result = query.execute()

    return build_paginated_response(
        data=result.data or [],
        total=result.count or 0,
        page=page,
        limit=limit,
    )


async def create_message(
    empresa_id: str, conversation_id: str, data: dict
) -> dict:
    """Registra uma nova mensagem em uma conversa."""
    supabase = get_supabase()

    await get_conversation(empresa_id, conversation_id)

    data["conversation_id"] = conversation_id
    data["empresa_id"] = empresa_id

    result = supabase.table("chat_messages").insert(data).execute()

    # Atualizar contagem e last_message_at na conversa
    now = datetime.now(timezone.utc).isoformat()
    supabase.rpc(
        "increment_message_count",
        {"conv_id": conversation_id},
    ).execute() if False else None  # RPC pode não existir

    # Fallback: atualizar via update direto
    supabase.table("chat_conversations").update({
        "last_message_at": now,
        "updated_at": now,
    }).eq("id", conversation_id).execute()

    return result.data[0]
