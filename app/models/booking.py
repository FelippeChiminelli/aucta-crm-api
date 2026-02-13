from pydantic import BaseModel, Field


# =====================================================
# Response Models
# =====================================================


class BookingAvailabilityResponse(BaseModel):
    """Janela de disponibilidade de uma agenda (dia/hora)."""

    id: str
    calendar_id: str
    day_of_week: int
    start_time: str
    end_time: str
    is_active: bool


class BookingTypeResponse(BaseModel):
    """Tipo de agendamento disponível em uma agenda."""

    id: str
    calendar_id: str
    name: str
    description: str | None = None
    duration_minutes: int
    buffer_before_minutes: int | None = 0
    buffer_after_minutes: int | None = 0
    color: str | None = None
    price: float | None = None
    max_per_day: int | None = None
    min_advance_hours: int | None = 1
    is_active: bool
    position: int | None = 0


class CalendarOwnerResponse(BaseModel):
    """Membro/responsável de uma agenda."""

    id: str
    calendar_id: str
    user_id: str
    role: str | None = "member"
    can_receive_bookings: bool | None = True
    booking_weight: int | None = 1


class CalendarResponse(BaseModel):
    """Agenda de agendamentos."""

    id: str
    empresa_id: str
    name: str
    description: str | None = None
    color: str | None = None
    timezone: str | None = "America/Sao_Paulo"
    is_active: bool | None = True
    is_public: bool | None = False
    public_slug: str | None = None
    min_advance_hours: int | None = 2
    max_advance_days: int | None = 30
    created_at: str
    updated_at: str
    # Relacionamentos opcionais
    booking_availability: list[BookingAvailabilityResponse] | None = None
    booking_types: list[BookingTypeResponse] | None = None
    booking_calendar_owners: list[CalendarOwnerResponse] | None = None


class BookingBlockResponse(BaseModel):
    """Bloqueio de horário em uma agenda."""

    id: str
    calendar_id: str
    start_datetime: str
    end_datetime: str
    reason: str | None = None


class BookingResponse(BaseModel):
    """Representação de um agendamento."""

    id: str
    empresa_id: str
    calendar_id: str
    booking_type_id: str
    assigned_to: str
    lead_id: str | None = None
    client_name: str | None = None
    client_phone: str | None = None
    client_email: str | None = None
    start_datetime: str
    end_datetime: str
    status: str | None = "confirmed"
    notes: str | None = None
    event_id: str | None = None
    created_by: str
    created_at: str
    updated_at: str
    # Relacionamentos opcionais
    booking_types: BookingTypeResponse | None = None


# =====================================================
# Request Models
# =====================================================


class CreateBookingRequest(BaseModel):
    """Dados para criar um novo agendamento."""

    calendar_id: str = Field(..., description="ID da agenda")
    booking_type_id: str = Field(..., description="ID do tipo de agendamento")
    assigned_to: str = Field(..., description="UUID do responsável pelo atendimento")
    created_by: str = Field(..., description="UUID de quem criou o agendamento")
    lead_id: str | None = Field(None, description="ID do lead associado")
    client_name: str | None = Field(None, max_length=200, description="Nome do cliente")
    client_phone: str | None = Field(None, max_length=20, description="Telefone do cliente")
    client_email: str | None = Field(None, description="Email do cliente")
    start_datetime: str = Field(..., description="Data/hora de início (ISO)")
    end_datetime: str = Field(..., description="Data/hora de fim (ISO)")
    status: str = Field("confirmed", description="Status (confirmed, pending, cancelled)")
    notes: str | None = Field(None, description="Observações")


class UpdateBookingRequest(BaseModel):
    """Dados para atualização parcial de um agendamento."""

    assigned_to: str | None = None
    lead_id: str | None = None
    client_name: str | None = Field(None, max_length=200)
    client_phone: str | None = Field(None, max_length=20)
    client_email: str | None = None
    start_datetime: str | None = None
    end_datetime: str | None = None
    status: str | None = None
    notes: str | None = None
