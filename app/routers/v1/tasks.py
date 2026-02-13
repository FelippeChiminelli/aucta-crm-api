from fastapi import APIRouter, Query

from app.core.dependencies import EmpresaId
from app.models.common import PaginatedResponse, SuccessResponse
from app.models.task import (
    CreateTaskCommentRequest,
    CreateTaskRequest,
    TaskCommentResponse,
    TaskResponse,
    TaskTypeResponse,
    UpdateTaskRequest,
)
from app.services import task_service

router = APIRouter()


# =====================================================
# Tasks CRUD
# =====================================================


@router.get("/tasks", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    empresa_id: EmpresaId,
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
    status: str | None = Query(None, description="Filtrar por status (pendente, em_andamento, concluida)"),
    priority: str | None = Query(None, description="Filtrar por prioridade (baixa, media, alta, urgente)"),
    assigned_to: str | None = Query(None, description="Filtrar por responsável (UUID)"),
    lead_id: str | None = Query(None, description="Filtrar por lead associado"),
    pipeline_id: str | None = Query(None, description="Filtrar por pipeline"),
    task_type_id: str | None = Query(None, description="Filtrar por tipo de tarefa"),
):
    """
    Lista tarefas da empresa com paginação e filtros.

    Ordenadas por data de vencimento (mais próximas primeiro).
    """
    return await task_service.list_tasks(
        empresa_id=empresa_id,
        page=page,
        limit=limit,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        lead_id=lead_id,
        pipeline_id=pipeline_id,
        task_type_id=task_type_id,
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, empresa_id: EmpresaId):
    """Busca uma tarefa por ID, incluindo o tipo de tarefa associado."""
    return await task_service.get_task(empresa_id, task_id)


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(data: CreateTaskRequest, empresa_id: EmpresaId):
    """
    Cria uma nova tarefa.

    Campos obrigatórios: `title` e `created_by`.
    """
    return await task_service.create_task(
        empresa_id, data.model_dump(exclude_none=True)
    )


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, data: UpdateTaskRequest, empresa_id: EmpresaId
):
    """Atualiza parcialmente uma tarefa. Envie apenas os campos que deseja alterar."""
    return await task_service.update_task(
        empresa_id, task_id, data.model_dump(exclude_none=True)
    )


@router.delete("/tasks/{task_id}", response_model=SuccessResponse)
async def delete_task(task_id: str, empresa_id: EmpresaId):
    """Deleta uma tarefa permanentemente."""
    await task_service.delete_task(empresa_id, task_id)
    return SuccessResponse(message="Tarefa deletada com sucesso")


# =====================================================
# Status transitions
# =====================================================


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: str, empresa_id: EmpresaId):
    """
    Marca uma tarefa como concluída.

    Define o status como 'concluida' e registra a data de conclusão.
    """
    return await task_service.complete_task(empresa_id, task_id)


@router.post("/tasks/{task_id}/reopen", response_model=TaskResponse)
async def reopen_task(task_id: str, empresa_id: EmpresaId):
    """
    Reabre uma tarefa concluída.

    Define o status como 'pendente' e remove a data de conclusão.
    """
    return await task_service.reopen_task(empresa_id, task_id)


# =====================================================
# Comments
# =====================================================


@router.get(
    "/tasks/{task_id}/comments", response_model=list[TaskCommentResponse]
)
async def list_comments(task_id: str, empresa_id: EmpresaId):
    """Lista todos os comentários de uma tarefa, ordenados por data."""
    return await task_service.list_comments(empresa_id, task_id)


@router.post(
    "/tasks/{task_id}/comments",
    response_model=TaskCommentResponse,
    status_code=201,
)
async def create_comment(
    task_id: str, data: CreateTaskCommentRequest, empresa_id: EmpresaId
):
    """Adiciona um comentário a uma tarefa."""
    return await task_service.create_comment(
        empresa_id, task_id, data.model_dump()
    )


# =====================================================
# Task Types
# =====================================================


@router.get("/task-types", response_model=list[TaskTypeResponse])
async def list_task_types(empresa_id: EmpresaId):
    """Lista todos os tipos de tarefa ativos da empresa."""
    return await task_service.list_task_types(empresa_id)
