from datetime import datetime, timezone
from urllib.parse import urlparse

from app.core.exceptions import NotFoundException, ValidationException
from app.utils.pagination import build_paginated_response, paginate_query
from app.utils.supabase_client import get_supabase

PRODUCT_SELECT = (
    "id, empresa_id, nome, descricao, sku, categoria_id, marca, preco, "
    "preco_promocional, quantidade_estoque, unidade_medida, status, tipo, "
    "duracao_estimada, recorrencia, created_at, updated_at, "
    "category:product_categories(id, empresa_id, nome, descricao, created_at), "
    "images:product_images(id, product_id, empresa_id, url, position, created_at)"
)

SOLD_STATUS = "vendido"
ACTIVE_STATUS = "ativo"
PRODUCT_IMAGES_BUCKET = "product-images"


# =====================================================
# Helpers
# =====================================================


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_product(product: dict) -> dict:
    """Ordena imagens por position (espelha o comportamento do frontend)."""
    images = product.get("images") or []
    images.sort(key=lambda img: img.get("position", 0))
    product["images"] = images
    return product


def _apply_filters(
    query,
    *,
    search: str | None,
    categoria_id: str | None,
    tipo: str | None,
    status_list: list[str] | None,
    marca_list: list[str] | None,
    preco_min: float | None,
    preco_max: float | None,
    only_promotion: bool,
    status_produto: str | None,
):
    """Replica `applyProductFilters` do frontend (productService.ts)."""
    if search:
        like = f"%{search}%"
        query = query.or_(
            f"nome.ilike.{like},descricao.ilike.{like},sku.ilike.{like},marca.ilike.{like}"
        )

    if categoria_id:
        query = query.eq("categoria_id", categoria_id)

    if tipo:
        query = query.eq("tipo", tipo)

    if marca_list:
        query = query.in_("marca", marca_list)

    if status_list:
        query = query.in_("status", status_list)

    # Filtro de disponibilidade — espelha status_veiculo do estoque de veículos
    if status_produto == "vendido":
        query = query.eq("status", SOLD_STATUS)
    elif status_produto == "todos":
        pass
    elif not status_list:
        query = query.neq("status", SOLD_STATUS)

    if preco_min is not None:
        query = query.gte("preco", preco_min)
    if preco_max is not None:
        query = query.lte("preco", preco_max)

    if only_promotion:
        query = query.not_.is_("preco_promocional", "null")

    return query


_SORT_MAP = {
    "preco_asc": ("preco", True),
    "preco_desc": ("preco", False),
    "nome_asc": ("nome", True),
    "nome_desc": ("nome", False),
    "created_desc": ("created_at", False),
    "created_asc": ("created_at", True),
    "estoque_asc": ("quantidade_estoque", True),
    "estoque_desc": ("quantidade_estoque", False),
}


def _apply_sort(query, sort_by: str | None):
    if not sort_by:
        return query.order("created_at", desc=True)

    sort = _SORT_MAP.get(sort_by)
    if not sort:
        return query.order("created_at", desc=True)

    column, ascending = sort
    return query.order(column, desc=not ascending, nullsfirst=False)


# =====================================================
# CRUD
# =====================================================


async def list_products(
    empresa_id: str,
    *,
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    categoria_id: str | None = None,
    tipo: str | None = None,
    status: list[str] | None = None,
    marca: list[str] | None = None,
    preco_min: float | None = None,
    preco_max: float | None = None,
    only_promotion: bool = False,
    status_produto: str | None = None,
    sort_by: str | None = None,
) -> dict:
    """Lista produtos/serviços da empresa com paginação e filtros."""
    supabase = get_supabase()

    query = (
        supabase.table("products")
        .select(PRODUCT_SELECT, count="exact")
        .eq("empresa_id", empresa_id)
    )

    query = _apply_filters(
        query,
        search=search,
        categoria_id=categoria_id,
        tipo=tipo,
        status_list=status,
        marca_list=marca,
        preco_min=preco_min,
        preco_max=preco_max,
        only_promotion=only_promotion,
        status_produto=status_produto,
    )
    query = _apply_sort(query, sort_by)
    query = paginate_query(query, page, limit)

    result = query.execute()

    products = [_normalize_product(p) for p in (result.data or [])]

    return build_paginated_response(
        data=products,
        total=result.count or 0,
        page=page,
        limit=limit,
    )


async def get_product(empresa_id: str, product_id: str) -> dict:
    """Busca um produto/serviço por ID."""
    supabase = get_supabase()

    result = (
        supabase.table("products")
        .select(PRODUCT_SELECT)
        .eq("id", product_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise NotFoundException(f"Produto '{product_id}' não encontrado")

    return _normalize_product(result.data[0])


async def create_product(empresa_id: str, data: dict) -> dict:
    """Cria um novo produto/serviço."""
    supabase = get_supabase()

    data["empresa_id"] = empresa_id

    result = supabase.table("products").insert(data).execute()
    return await get_product(empresa_id, result.data[0]["id"])


async def update_product(empresa_id: str, product_id: str, data: dict) -> dict:
    """Atualiza parcialmente um produto/serviço."""
    supabase = get_supabase()

    await get_product(empresa_id, product_id)

    data["updated_at"] = _now_iso()
    supabase.table("products").update(data).eq("id", product_id).eq(
        "empresa_id", empresa_id
    ).execute()

    return await get_product(empresa_id, product_id)


async def delete_product(empresa_id: str, product_id: str) -> None:
    """Deleta um produto/serviço (e remove imagens associadas do storage)."""
    supabase = get_supabase()

    await get_product(empresa_id, product_id)

    images = (
        supabase.table("product_images")
        .select("url")
        .eq("product_id", product_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    for image in images.data or []:
        _delete_image_from_storage(image.get("url"))

    supabase.table("products").delete().eq("id", product_id).eq(
        "empresa_id", empresa_id
    ).execute()


# =====================================================
# Ações especiais
# =====================================================


async def mark_product_as_sold(
    empresa_id: str, product_id: str, quantidade_vendida: int = 1
) -> dict:
    """Marca um produto como vendido (espelha productSaleService.markProductAsSold).

    - Serviço (`tipo='servico'`): muda status para `vendido` sem mexer em estoque.
    - Produto: decrementa estoque; quando chega a 0, status vira `vendido`.
    """
    if quantidade_vendida <= 0:
        raise ValidationException("A quantidade vendida deve ser maior que zero")

    supabase = get_supabase()
    product = await get_product(empresa_id, product_id)

    is_service = (product.get("tipo") or "produto") == "servico"
    now = _now_iso()

    if is_service:
        update_payload = {"status": SOLD_STATUS, "updated_at": now}
    else:
        estoque_atual = product.get("quantidade_estoque") or 0
        novo_estoque = max(0, estoque_atual - quantidade_vendida)
        novo_status = SOLD_STATUS if novo_estoque == 0 else ACTIVE_STATUS
        update_payload = {
            "quantidade_estoque": novo_estoque,
            "status": novo_status,
            "updated_at": now,
        }

    supabase.table("products").update(update_payload).eq("id", product_id).eq(
        "empresa_id", empresa_id
    ).execute()

    return await get_product(empresa_id, product_id)


async def mark_product_as_available(empresa_id: str, product_id: str) -> dict:
    """Recoloca um produto/serviço como disponível (status `ativo`)."""
    supabase = get_supabase()
    await get_product(empresa_id, product_id)

    supabase.table("products").update(
        {"status": ACTIVE_STATUS, "updated_at": _now_iso()}
    ).eq("id", product_id).eq("empresa_id", empresa_id).execute()

    return await get_product(empresa_id, product_id)


async def adjust_stock(
    empresa_id: str,
    product_id: str,
    *,
    delta: int | None = None,
    quantidade_estoque: int | None = None,
) -> dict:
    """Ajusta o estoque por delta (relativo) ou valor absoluto."""
    supabase = get_supabase()
    product = await get_product(empresa_id, product_id)

    if quantidade_estoque is not None:
        novo_estoque = quantidade_estoque
    else:
        atual = product.get("quantidade_estoque") or 0
        novo_estoque = atual + (delta or 0)

    if novo_estoque < 0:
        raise ValidationException("Estoque não pode ficar negativo")

    supabase.table("products").update(
        {"quantidade_estoque": novo_estoque, "updated_at": _now_iso()}
    ).eq("id", product_id).eq("empresa_id", empresa_id).execute()

    return await get_product(empresa_id, product_id)


# =====================================================
# Storage helpers
# =====================================================


def _delete_image_from_storage(image_url: str | None) -> None:
    """Remove um arquivo do bucket `product-images` a partir da URL pública."""
    if not image_url:
        return
    try:
        parsed = urlparse(image_url)
        marker = f"/{PRODUCT_IMAGES_BUCKET}/"
        idx = parsed.path.find(marker)
        if idx == -1:
            return
        object_path = parsed.path[idx + len(marker):]
        if object_path:
            get_supabase().storage.from_(PRODUCT_IMAGES_BUCKET).remove([object_path])
    except Exception:
        # Falha em remover do storage não deve bloquear o delete do registro
        pass
