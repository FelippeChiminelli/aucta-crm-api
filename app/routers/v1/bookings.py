from fastapi import APIRouter, Query

from app.core.dependencies import EmpresaId
from app.models.booking import (
    BookingAvailabilityResponse,
    BookingBlockResponse,
    BookingResponse,
    BookingTypeResponse,
    CalendarOwnerResponse,
    CalendarResponse,
    CreateBookingRequest,
    UpdateBookingRequest,
)
from app.models.common import PaginatedResponse, SuccessResponse
from app.services import booking_service

router = APIRouter()


# =====================================================
# Calendars (somente leitura)
# =====================================================


@router.get("/bookings/calendars", response_model=list[CalendarResponse])
async def list_calendars(empresa_id: EmpresaId):
    """Lista todas as agendas ativas da empresa."""
    return await booking_service.list_calendars(empresa_id)


@router.get("/bookings/calendars/{calendar_id}", response_model=CalendarResponse)
async def get_calendar(calendar_id: str, empresa_id: EmpresaId):
    """
    Busca uma agenda por ID.

    Retorna a agenda com disponibilidade, tipos de agendamento e membros.
    """
    return await booking_service.get_calendar(empresa_id, calendar_id)


@router.get(
    "/bookings/calendars/{calendar_id}/availability",
    response_model=list[BookingAvailabilityResponse],
)
async def list_availability(calendar_id: str, empresa_id: EmpresaId):
    """
    Lista horários de disponibilidade de uma agenda.

    `day_of_week`: 0 = Domingo, 1 = Segunda, ..., 6 = Sábado.
    """
    return await booking_service.list_availability(empresa_id, calendar_id)


@router.get(
    "/bookings/calendars/{calendar_id}/types",
    response_model=list[BookingTypeResponse],
)
async def list_booking_types(calendar_id: str, empresa_id: EmpresaId):
    """Lista tipos de agendamento ativos de uma agenda."""
    return await booking_service.list_booking_types(empresa_id, calendar_id)


@router.get(
    "/bookings/calendars/{calendar_id}/blocks",
    response_model=list[BookingBlockResponse],
)
async def list_blocks(
    calendar_id: str,
    empresa_id: EmpresaId,
    date_from: str | None = Query(None, description="Filtrar a partir de data (ISO)"),
):
    """Lista bloqueios de horário de uma agenda."""
    return await booking_service.list_blocks(empresa_id, calendar_id, date_from)


# =====================================================
# Bookings CRUD
# =====================================================


@router.get("/bookings", response_model=PaginatedResponse[BookingResponse])
async def list_bookings(
    empresa_id: EmpresaId,
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
    calendar_id: str | None = Query(None, description="Filtrar por agenda"),
    status: str | None = Query(None, description="Filtrar por status (confirmed, pending, cancelled)"),
    assigned_to: str | None = Query(None, description="Filtrar por responsável (UUID)"),
    lead_id: str | None = Query(None, description="Filtrar por lead associado"),
    date_from: str | None = Query(None, description="Data/hora inicial (ISO)"),
    date_to: str | None = Query(None, description="Data/hora final (ISO)"),
):
    """
    Lista agendamentos da empresa com paginação e filtros.

    Ordenados por data de início (mais próximos primeiro).
    """
    return await booking_service.list_bookings(
        empresa_id=empresa_id,
        page=page,
        limit=limit,
        calendar_id=calendar_id,
        status=status,
        assigned_to=assigned_to,
        lead_id=lead_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: str, empresa_id: EmpresaId):
    """Busca um agendamento por ID, incluindo o tipo de agendamento."""
    return await booking_service.get_booking(empresa_id, booking_id)


@router.post("/bookings", response_model=BookingResponse, status_code=201)
async def create_booking(data: CreateBookingRequest, empresa_id: EmpresaId):
    """
    Cria um novo agendamento.

    Campos obrigatórios: `calendar_id`, `booking_type_id`, `assigned_to`,
    `created_by`, `start_datetime`, `end_datetime`.
    """
    return await booking_service.create_booking(
        empresa_id, data.model_dump(exclude_none=True)
    )


@router.patch("/bookings/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: str, data: UpdateBookingRequest, empresa_id: EmpresaId
):
    """Atualiza parcialmente um agendamento."""
    return await booking_service.update_booking(
        empresa_id, booking_id, data.model_dump(exclude_none=True)
    )


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(booking_id: str, empresa_id: EmpresaId):
    """Cancela um agendamento. Define o status como 'cancelled'."""
    return await booking_service.cancel_booking(empresa_id, booking_id)


@router.post("/bookings/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(booking_id: str, empresa_id: EmpresaId):
    """Confirma um agendamento pendente. Define o status como 'confirmed'."""
    return await booking_service.confirm_booking(empresa_id, booking_id)


@router.delete("/bookings/{booking_id}", response_model=SuccessResponse)
async def delete_booking(booking_id: str, empresa_id: EmpresaId):
    """Deleta um agendamento permanentemente."""
    await booking_service.delete_booking(empresa_id, booking_id)
    return SuccessResponse(message="Agendamento deletado com sucesso")
