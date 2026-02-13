from fastapi import APIRouter, Query

from app.core.dependencies import EmpresaId
from app.models.chat import (
    ConversationResponse,
    CreateConversationRequest,
    CreateMessageRequest,
    MessageResponse,
    UpdateConversationRequest,
    WhatsappInstanceResponse,
)
from app.models.common import PaginatedResponse
from app.services import chat_service

router = APIRouter()


# =====================================================
# WhatsApp Instances (somente leitura)
# =====================================================


@router.get("/chat/instances", response_model=list[WhatsappInstanceResponse])
async def list_instances(empresa_id: EmpresaId):
    """Lista instâncias de WhatsApp conectadas à empresa."""
    return await chat_service.list_instances(empresa_id)


# =====================================================
# Conversations
# =====================================================


@router.get(
    "/chat/conversations",
    response_model=PaginatedResponse[ConversationResponse],
)
async def list_conversations(
    empresa_id: EmpresaId,
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
    status: str | None = Query(None, description="Filtrar por status (active, closed, archived)"),
    instance_id: str | None = Query(None, description="Filtrar por instância WhatsApp"),
    lead_id: str | None = Query(None, description="Filtrar por lead"),
    assigned_user_id: str | None = Query(None, description="Filtrar por atendente (UUID)"),
    fone: str | None = Query(None, description="Filtrar por telefone"),
):
    """
    Lista conversas da empresa com paginação e filtros.

    Ordenadas pela última mensagem (mais recentes primeiro).
    """
    return await chat_service.list_conversations(
        empresa_id=empresa_id,
        page=page,
        limit=limit,
        status=status,
        instance_id=instance_id,
        lead_id=lead_id,
        assigned_user_id=assigned_user_id,
        fone=fone,
    )


@router.get(
    "/chat/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
async def get_conversation(conversation_id: str, empresa_id: EmpresaId):
    """Busca uma conversa por ID."""
    return await chat_service.get_conversation(empresa_id, conversation_id)


@router.post(
    "/chat/conversations",
    response_model=ConversationResponse,
    status_code=201,
)
async def create_conversation(
    data: CreateConversationRequest, empresa_id: EmpresaId
):
    """
    Cria uma nova conversa.

    Pode ser vinculada a um lead e/ou instância WhatsApp.
    """
    return await chat_service.create_conversation(
        empresa_id, data.model_dump(exclude_none=True)
    )


@router.patch(
    "/chat/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
async def update_conversation(
    conversation_id: str,
    data: UpdateConversationRequest,
    empresa_id: EmpresaId,
):
    """Atualiza parcialmente uma conversa (atendente, status, etc.)."""
    return await chat_service.update_conversation(
        empresa_id, conversation_id, data.model_dump(exclude_none=True)
    )


@router.post(
    "/chat/conversations/{conversation_id}/close",
    response_model=ConversationResponse,
)
async def close_conversation(conversation_id: str, empresa_id: EmpresaId):
    """Encerra uma conversa. Define o status como 'closed'."""
    return await chat_service.close_conversation(empresa_id, conversation_id)


# =====================================================
# Messages
# =====================================================


@router.get(
    "/chat/conversations/{conversation_id}/messages",
    response_model=PaginatedResponse[MessageResponse],
)
async def list_messages(
    conversation_id: str,
    empresa_id: EmpresaId,
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(50, ge=1, le=100, description="Mensagens por página"),
):
    """
    Lista mensagens de uma conversa com paginação.

    Ordenadas cronologicamente (mais antigas primeiro).
    """
    return await chat_service.list_messages(
        empresa_id, conversation_id, page, limit
    )


@router.post(
    "/chat/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=201,
)
async def create_message(
    conversation_id: str,
    data: CreateMessageRequest,
    empresa_id: EmpresaId,
):
    """
    Registra uma nova mensagem em uma conversa.

    Tipos suportados: `text`, `image`, `audio`, `video`, `document`.
    Direções: `inbound` (recebida) e `outbound` (enviada).
    """
    return await chat_service.create_message(
        empresa_id, conversation_id, data.model_dump(exclude_none=True)
    )
