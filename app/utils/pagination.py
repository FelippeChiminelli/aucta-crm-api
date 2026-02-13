import math


def paginate_query(query, page: int, limit: int):
    """
    Aplica paginação a uma query do Supabase.

    Args:
        query: Query builder do Supabase (antes do .execute())
        page: Número da página (1-indexed)
        limit: Quantidade de itens por página

    Returns:
        Query com range aplicado
    """
    offset = (page - 1) * limit
    return query.range(offset, offset + limit - 1)


def build_paginated_response(data: list, total: int, page: int, limit: int) -> dict:
    """
    Monta o dict de resposta paginada.

    Args:
        data: Lista de items retornados
        total: Total de items no banco
        page: Página atual
        limit: Limite por página

    Returns:
        Dict compatível com PaginatedResponse
    """
    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total / limit) if limit > 0 else 0,
    }
