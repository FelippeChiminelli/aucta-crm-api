from fastapi import APIRouter

from app.core.dependencies import EmpresaId
from app.models.user import UserResponse
from app.services import user_service

router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
async def list_users(empresa_id: EmpresaId):
    """
    Lista usuários da empresa.

    Retorna apenas dados públicos (nome, email, telefone) para uso
    na atribuição de responsáveis aos leads.
    """
    return await user_service.list_users(empresa_id)
