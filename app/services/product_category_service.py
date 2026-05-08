from app.core.exceptions import NotFoundException
from app.utils.supabase_client import get_supabase

CATEGORY_SELECT = "id, empresa_id, nome, descricao, created_at"


async def list_categories(empresa_id: str) -> list[dict]:
    """Lista todas as categorias de produtos/serviços da empresa."""
    supabase = get_supabase()

    result = (
        supabase.table("product_categories")
        .select(CATEGORY_SELECT)
        .eq("empresa_id", empresa_id)
        .order("nome")
        .execute()
    )
    return result.data or []


async def get_category(empresa_id: str, category_id: str) -> dict:
    """Busca uma categoria por ID."""
    supabase = get_supabase()

    result = (
        supabase.table("product_categories")
        .select(CATEGORY_SELECT)
        .eq("id", category_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise NotFoundException(f"Categoria '{category_id}' não encontrada")

    return result.data[0]


async def create_category(empresa_id: str, data: dict) -> dict:
    """Cria uma nova categoria."""
    supabase = get_supabase()

    data["empresa_id"] = empresa_id
    result = supabase.table("product_categories").insert(data).execute()
    return await get_category(empresa_id, result.data[0]["id"])


async def update_category(empresa_id: str, category_id: str, data: dict) -> dict:
    """Atualiza parcialmente uma categoria."""
    supabase = get_supabase()
    await get_category(empresa_id, category_id)

    supabase.table("product_categories").update(data).eq("id", category_id).eq(
        "empresa_id", empresa_id
    ).execute()

    return await get_category(empresa_id, category_id)


async def delete_category(empresa_id: str, category_id: str) -> None:
    """Deleta uma categoria permanentemente."""
    supabase = get_supabase()
    await get_category(empresa_id, category_id)

    supabase.table("product_categories").delete().eq("id", category_id).eq(
        "empresa_id", empresa_id
    ).execute()
