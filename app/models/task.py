from pydantic import BaseModel, Field


# =====================================================
# Response Models
# =====================================================


class TaskTypeResponse(BaseModel):
    """Tipo de tarefa configurado na empresa."""

    id: str
    name: str
    color: str
    icon: str | None = None
    active: bool


class TaskCommentResponse(BaseModel):
    """Comentário em uma tarefa."""

    id: str
    task_id: str
    user_id: str
    comment: str
    type: str | None = "comment"
    metadata: dict | None = None
    created_at: str


class TaskResponse(BaseModel):
    """Representação completa de uma tarefa na resposta da API."""

    id: str
    title: str
    description: str | None = None
    empresa_id: str
    assigned_to: str | None = None
    created_by: str
    lead_id: str | None = None
    pipeline_id: str | None = None
    task_type_id: str | None = None
    status: str
    priority: str
    due_date: str | None = None
    due_time: str | None = None
    completed_at: str | None = None
    started_at: str | None = None
    tags: list[str] | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    created_at: str
    updated_at: str
    # Relacionamentos opcionais
    task_types: TaskTypeResponse | None = None


# =====================================================
# Request Models
# =====================================================


class CreateTaskRequest(BaseModel):
    """Dados para criação de uma nova tarefa."""

    title: str = Field(..., min_length=1, max_length=300, description="Título da tarefa")
    description: str | None = Field(None, description="Descrição detalhada")
    assigned_to: str | None = Field(None, description="UUID do responsável")
    created_by: str = Field(..., description="UUID do criador da tarefa")
    lead_id: str | None = Field(None, description="ID do lead associado")
    pipeline_id: str | None = Field(None, description="ID do pipeline associado")
    task_type_id: str | None = Field(None, description="ID do tipo de tarefa")
    status: str = Field("pendente", description="Status (pendente, em_andamento, concluida)")
    priority: str = Field("media", description="Prioridade (baixa, media, alta, urgente)")
    due_date: str | None = Field(None, description="Data de vencimento (ISO)")
    due_time: str | None = Field(None, description="Horário de vencimento (HH:MM)")
    tags: list[str] | None = Field(None, description="Tags da tarefa")
    estimated_hours: float | None = Field(None, ge=0, description="Horas estimadas")


class UpdateTaskRequest(BaseModel):
    """Dados para atualização parcial de uma tarefa."""

    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    assigned_to: str | None = None
    lead_id: str | None = None
    pipeline_id: str | None = None
    task_type_id: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: str | None = None
    due_time: str | None = None
    tags: list[str] | None = None
    estimated_hours: float | None = Field(None, ge=0)
    actual_hours: float | None = Field(None, ge=0)


class CreateTaskCommentRequest(BaseModel):
    """Dados para adicionar um comentário a uma tarefa."""

    user_id: str = Field(..., description="UUID do usuário que comenta")
    comment: str = Field(..., min_length=1, description="Texto do comentário")
