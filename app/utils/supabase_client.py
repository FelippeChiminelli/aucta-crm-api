from supabase import create_client, Client
from app.core.config import get_settings

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Retorna uma instância singleton do cliente Supabase usando a service role key."""
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase_client
