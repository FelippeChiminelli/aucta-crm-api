from app.utils.supabase_client import get_supabase

USER_SELECT = "uuid, full_name, email, phone"


async def list_users(empresa_id: str) -> list[dict]:
    """Lista usuários da empresa (dados públicos para atribuição de leads)."""
    supabase = get_supabase()

    result = (
        supabase.table("profiles")
        .select(USER_SELECT)
        .eq("empresa_id", empresa_id)
        .order("full_name")
        .execute()
    )

    return result.data or []
