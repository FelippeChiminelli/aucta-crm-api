from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.utils.pagination import build_paginated_response, paginate_query
from app.utils.supabase_client import get_supabase

CALENDAR_SELECT = (
    "id, empresa_id, name, description, color, timezone, is_active, "
    "is_public, public_slug, min_advance_hours, max_advance_days, "
    "created_at, updated_at"
)

AVAILABILITY_SELECT = "id, calendar_id, day_of_week, start_time, end_time, is_active"

BOOKING_TYPE_SELECT = (
    "id, calendar_id, name, description, duration_minutes, "
    "buffer_before_minutes, buffer_after_minutes, color, price, "
    "max_per_day, min_advance_hours, is_active, position"
)

OWNER_SELECT = "id, calendar_id, user_id, role, can_receive_bookings, booking_weight"

BLOCK_SELECT = "id, calendar_id, start_datetime, end_datetime, reason"

BOOKING_SELECT = (
    "id, empresa_id, calendar_id, booking_type_id, assigned_to, "
    "lead_id, client_name, client_phone, client_email, "
    "start_datetime, end_datetime, status, notes, event_id, "
    "created_by, created_at, updated_at, "
    "booking_types(" + BOOKING_TYPE_SELECT + ")"
)


# =====================================================
# Calendars (somente leitura)
# =====================================================


async def list_calendars(empresa_id: str) -> list[dict]:
    """Lista agendas ativas da empresa."""
    supabase = get_supabase()

    result = (
        supabase.table("booking_calendars")
        .select(CALENDAR_SELECT)
        .eq("empresa_id", empresa_id)
        .eq("is_active", True)
        .order("name")
        .execute()
    )

    return result.data or []


async def get_calendar(empresa_id: str, calendar_id: str) -> dict:
    """Busca uma agenda com disponibilidade, tipos e membros."""
    supabase = get_supabase()

    select = (
        f"{CALENDAR_SELECT}, "
        f"booking_availability({AVAILABILITY_SELECT}), "
        f"booking_types({BOOKING_TYPE_SELECT}), "
        f"booking_calendar_owners({OWNER_SELECT})"
    )

    result = (
        supabase.table("booking_calendars")
        .select(select)
        .eq("id", calendar_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise NotFoundException(f"Agenda '{calendar_id}' não encontrada")

    calendar = result.data[0]

    # Ordenar availability por dia e horário
    if calendar.get("booking_availability"):
        calendar["booking_availability"].sort(
            key=lambda a: (a.get("day_of_week", 0), a.get("start_time", ""))
        )

    # Ordenar types por position
    if calendar.get("booking_types"):
        calendar["booking_types"].sort(key=lambda t: t.get("position", 0))

    return calendar


async def list_availability(empresa_id: str, calendar_id: str) -> list[dict]:
    """Lista horários de disponibilidade de uma agenda."""
    supabase = get_supabase()

    # Validar que a agenda pertence à empresa
    await get_calendar(empresa_id, calendar_id)

    result = (
        supabase.table("booking_availability")
        .select(AVAILABILITY_SELECT)
        .eq("calendar_id", calendar_id)
        .eq("is_active", True)
        .order("day_of_week")
        .execute()
    )

    return result.data or []


async def list_booking_types(empresa_id: str, calendar_id: str) -> list[dict]:
    """Lista tipos de agendamento ativos de uma agenda."""
    supabase = get_supabase()

    await get_calendar(empresa_id, calendar_id)

    result = (
        supabase.table("booking_types")
        .select(BOOKING_TYPE_SELECT)
        .eq("calendar_id", calendar_id)
        .eq("is_active", True)
        .order("position")
        .execute()
    )

    return result.data or []


async def list_blocks(
    empresa_id: str, calendar_id: str, date_from: str | None = None
) -> list[dict]:
    """Lista bloqueios de horário de uma agenda."""
    supabase = get_supabase()

    await get_calendar(empresa_id, calendar_id)

    query = (
        supabase.table("booking_blocks")
        .select(BLOCK_SELECT)
        .eq("calendar_id", calendar_id)
        .order("start_datetime")
    )

    if date_from:
        query = query.gte("start_datetime", date_from)

    return (query.execute()).data or []


# =====================================================
# Bookings CRUD
# =====================================================


async def list_bookings(
    empresa_id: str,
    page: int = 1,
    limit: int = 20,
    calendar_id: str | None = None,
    status: str | None = None,
    assigned_to: str | None = None,
    lead_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """Lista agendamentos da empresa com paginação e filtros."""
    supabase = get_supabase()

    query = (
        supabase.table("bookings")
        .select(BOOKING_SELECT, count="exact")
        .eq("empresa_id", empresa_id)
    )

    if calendar_id:
        query = query.eq("calendar_id", calendar_id)
    if status:
        query = query.eq("status", status)
    if assigned_to:
        query = query.eq("assigned_to", assigned_to)
    if lead_id:
        query = query.eq("lead_id", lead_id)
    if date_from:
        query = query.gte("start_datetime", date_from)
    if date_to:
        query = query.lte("start_datetime", date_to)

    query = query.order("start_datetime", desc=False)
    query = paginate_query(query, page, limit)

    result = query.execute()

    return build_paginated_response(
        data=result.data or [],
        total=result.count or 0,
        page=page,
        limit=limit,
    )


async def get_booking(empresa_id: str, booking_id: str) -> dict:
    """Busca um agendamento por ID."""
    supabase = get_supabase()

    result = (
        supabase.table("bookings")
        .select(BOOKING_SELECT)
        .eq("id", booking_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise NotFoundException(f"Agendamento '{booking_id}' não encontrado")

    return result.data[0]


async def create_booking(empresa_id: str, data: dict) -> dict:
    """Cria um novo agendamento."""
    supabase = get_supabase()

    data["empresa_id"] = empresa_id

    result = supabase.table("bookings").insert(data).execute()

    return await get_booking(empresa_id, result.data[0]["id"])


async def update_booking(empresa_id: str, booking_id: str, data: dict) -> dict:
    """Atualiza parcialmente um agendamento."""
    supabase = get_supabase()

    await get_booking(empresa_id, booking_id)

    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    supabase.table("bookings").update(data).eq("id", booking_id).execute()

    return await get_booking(empresa_id, booking_id)


async def cancel_booking(empresa_id: str, booking_id: str) -> dict:
    """Cancela um agendamento."""
    supabase = get_supabase()

    await get_booking(empresa_id, booking_id)

    now = datetime.now(timezone.utc).isoformat()
    supabase.table("bookings").update({
        "status": "cancelled",
        "updated_at": now,
    }).eq("id", booking_id).execute()

    return await get_booking(empresa_id, booking_id)


async def confirm_booking(empresa_id: str, booking_id: str) -> dict:
    """Confirma um agendamento pendente."""
    supabase = get_supabase()

    await get_booking(empresa_id, booking_id)

    now = datetime.now(timezone.utc).isoformat()
    supabase.table("bookings").update({
        "status": "confirmed",
        "updated_at": now,
    }).eq("id", booking_id).execute()

    return await get_booking(empresa_id, booking_id)


async def delete_booking(empresa_id: str, booking_id: str) -> None:
    """Deleta um agendamento permanentemente."""
    supabase = get_supabase()

    await get_booking(empresa_id, booking_id)

    supabase.table("bookings").delete().eq("id", booking_id).execute()
