from fastapi import APIRouter

from app.core.dependencies import EmpresaId
from app.models.vehicle import VehicleResponse
from app.services import vehicle_service

router = APIRouter()


@router.get("/vehicles", response_model=list[VehicleResponse])
async def list_vehicles(empresa_id: EmpresaId):
    """
    Retorna todo o estoque de veículos da empresa.

    A `empresa_id` é extraída automaticamente do token de API
    enviado no header `Authorization: Bearer <token>`.

    Cada veículo inclui suas imagens ordenadas por posição.
    """
    return await vehicle_service.list_vehicles(empresa_id)
