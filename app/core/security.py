from datetime import datetime, timezone

from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import UnauthorizedException
from app.utils.supabase_client import get_supabase

security_scheme = HTTPBearer(
    scheme_name="API Token",
    description="Token de API gerado no painel do CRM. Formato: adv_live_xxxxxxxx",
)


async def validate_api_token(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> str:
    """
    Valida o token de API e retorna o empresa_id associado.

    Busca na tabela api_tokens onde token = X AND is_active = true.
    Atualiza last_used_at para rastreamento de uso.

    Returns:
        empresa_id (str): UUID da empresa associada ao token.

    Raises:
        UnauthorizedException: Se o token for inválido ou inativo.
    """
    token = credentials.credentials

    if not token:
        raise UnauthorizedException("Token não fornecido")

    supabase = get_supabase()

    result = (
        supabase.table("api_tokens")
        .select("id, empresa_id, is_active")
        .eq("token", token)
        .eq("is_active", True)
        .execute()
    )

    if not result.data:
        raise UnauthorizedException("Token de API inválido ou desativado")

    token_data = result.data[0]

    # Atualiza last_used_at de forma assíncrona (fire-and-forget)
    supabase.table("api_tokens").update(
        {"last_used_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", token_data["id"]).execute()

    return token_data["empresa_id"]
