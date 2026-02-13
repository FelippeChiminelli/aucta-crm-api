from pydantic import BaseModel, Field


# =====================================================
# Response Models
# =====================================================


class WhatsappInstanceResponse(BaseModel):
    """Instância de WhatsApp conectada à empresa."""

    id: str
    name: str
    phone_number: str
    status: str
    display_name: str | None = None
    auto_create_leads: bool | None = False
    created_at: str
    updated_at: str


class ConversationResponse(BaseModel):
    """Representação de uma conversa de chat."""

    id: str
    empresa_id: str
    lead_id: str | None = None
    instance_id: str | None = None
    fone: str | None = None
    nome_instancia: str | None = None
    Nome_Whatsapp: str | None = Field(None, alias="Nome_Whatsapp")
    assigned_user_id: str | None = None
    cod_lid: str | None = None
    status: str
    last_message_at: str | None = None
    message_count: int | None = 0
    created_at: str
    updated_at: str

    model_config = {"populate_by_name": True}


class MessageResponse(BaseModel):
    """Representação de uma mensagem de chat."""

    id: str
    conversation_id: str
    instance_id: str | None = None
    message_type: str
    content: str | None = None
    media_url: str | None = None
    direction: str
    status: str
    timestamp: str | None = None
    empresa_id: str
    created_at: str


# =====================================================
# Request Models
# =====================================================


class CreateConversationRequest(BaseModel):
    """Dados para criar uma nova conversa."""

    lead_id: str | None = Field(None, description="ID do lead associado")
    instance_id: str | None = Field(None, description="ID da instância WhatsApp")
    fone: str | None = Field(None, max_length=20, description="Telefone do contato")
    nome_instancia: str | None = Field(None, description="Nome da instância")
    assigned_user_id: str | None = Field(None, description="UUID do atendente")
    cod_lid: str | None = Field(None, description="Código do lead")
    status: str = Field("active", description="Status (active, closed, archived)")


class UpdateConversationRequest(BaseModel):
    """Dados para atualização parcial de uma conversa."""

    lead_id: str | None = None
    assigned_user_id: str | None = None
    status: str | None = None
    cod_lid: str | None = None


class CreateMessageRequest(BaseModel):
    """Dados para enviar/registrar uma mensagem."""

    instance_id: str | None = Field(None, description="ID da instância WhatsApp")
    message_type: str = Field("text", description="Tipo (text, image, audio, video, document)")
    content: str | None = Field(None, description="Conteúdo textual da mensagem")
    media_url: str | None = Field(None, description="URL da mídia (se aplicável)")
    direction: str = Field(..., description="Direção (inbound, outbound)")
    status: str = Field("sent", description="Status (sent, delivered, read, failed)")
