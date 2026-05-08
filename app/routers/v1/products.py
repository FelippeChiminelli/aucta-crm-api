from fastapi import APIRouter, Query

from app.core.dependencies import EmpresaId
from app.models.common import PaginatedResponse, SuccessResponse
from app.models.product import (
    AdjustStockRequest,
    CreateCategoryRequest,
    CreateProductImageRequest,
    CreateProductRequest,
    MarkSoldRequest,
    ProductCategoryResponse,
    ProductImageResponse,
    ProductResponse,
    ProductStatus,
    ProductType,
    ReorderImagesRequest,
    SortBy,
    StatusProduto,
    UpdateCategoryRequest,
    UpdateProductRequest,
)
from app.services import (
    product_category_service,
    product_image_service,
    product_service,
)

router = APIRouter()


# =====================================================
# Produtos / Serviços — CRUD
# =====================================================


@router.get("/products", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    empresa_id: EmpresaId,
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
    search: str | None = Query(
        None, description="Busca textual em nome, descrição, SKU e marca"
    ),
    categoria_id: str | None = Query(None, description="Filtrar por categoria"),
    tipo: ProductType | None = Query(
        None, description="Filtrar por tipo: produto ou servico"
    ),
    status: list[ProductStatus] | None = Query(
        None, description="Filtrar por status (pode repetir)"
    ),
    marca: list[str] | None = Query(
        None, description="Filtrar por marca (pode repetir)"
    ),
    preco_min: float | None = Query(None, ge=0, description="Preço mínimo"),
    preco_max: float | None = Query(None, ge=0, description="Preço máximo"),
    only_promotion: bool = Query(
        False, description="Retornar apenas itens com preço promocional"
    ),
    status_produto: StatusProduto | None = Query(
        None,
        description=(
            "Disponibilidade — `ativo` (em estoque, default), `vendido`, ou `todos`"
        ),
    ),
    sort_by: SortBy | None = Query(None, description="Ordenação"),
):
    """
    Lista o estoque geral (produtos e serviços) da empresa com paginação e filtros.

    Por padrão, oculta itens com status `vendido`. Use `status_produto=todos`
    para incluí-los ou `status_produto=vendido` para listar apenas vendidos.
    """
    return await product_service.list_products(
        empresa_id,
        page=page,
        limit=limit,
        search=search,
        categoria_id=categoria_id,
        tipo=tipo,
        status=list(status) if status else None,
        marca=list(marca) if marca else None,
        preco_min=preco_min,
        preco_max=preco_max,
        only_promotion=only_promotion,
        status_produto=status_produto,
        sort_by=sort_by,
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, empresa_id: EmpresaId):
    """Busca um produto/serviço por ID, incluindo categoria e imagens."""
    return await product_service.get_product(empresa_id, product_id)


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(data: CreateProductRequest, empresa_id: EmpresaId):
    """Cria um novo produto ou serviço no estoque."""
    return await product_service.create_product(
        empresa_id, data.model_dump(exclude_none=True)
    )


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str, data: UpdateProductRequest, empresa_id: EmpresaId
):
    """Atualiza parcialmente um produto/serviço."""
    return await product_service.update_product(
        empresa_id, product_id, data.model_dump(exclude_unset=True)
    )


@router.delete("/products/{product_id}", response_model=SuccessResponse)
async def delete_product(product_id: str, empresa_id: EmpresaId):
    """Deleta um produto/serviço (e suas imagens) permanentemente."""
    await product_service.delete_product(empresa_id, product_id)
    return SuccessResponse(message="Produto deletado com sucesso")


# =====================================================
# Ações de venda / estoque
# =====================================================


@router.post("/products/{product_id}/mark-sold", response_model=ProductResponse)
async def mark_product_as_sold(
    product_id: str, data: MarkSoldRequest, empresa_id: EmpresaId
):
    """
    Marca um produto/serviço como vendido.

    - **Serviço**: muda status para `vendido` (estoque ignorado).
    - **Produto**: decrementa o estoque pela `quantidade_vendida`. Se chegar a 0,
      o status vira `vendido`; caso contrário, permanece `ativo`.
    """
    return await product_service.mark_product_as_sold(
        empresa_id, product_id, data.quantidade_vendida
    )


@router.post(
    "/products/{product_id}/mark-available", response_model=ProductResponse
)
async def mark_product_as_available(product_id: str, empresa_id: EmpresaId):
    """Recoloca um produto/serviço como disponível (status `ativo`)."""
    return await product_service.mark_product_as_available(empresa_id, product_id)


@router.post("/products/{product_id}/adjust-stock", response_model=ProductResponse)
async def adjust_stock(
    product_id: str, data: AdjustStockRequest, empresa_id: EmpresaId
):
    """
    Ajusta o estoque de um produto.

    Forneça apenas um dos campos:
    - `delta`: incrementa (positivo) ou decrementa (negativo) o estoque atual.
    - `quantidade_estoque`: define o estoque para um valor absoluto.
    """
    return await product_service.adjust_stock(
        empresa_id,
        product_id,
        delta=data.delta,
        quantidade_estoque=data.quantidade_estoque,
    )


# =====================================================
# Imagens
# =====================================================


@router.get(
    "/products/{product_id}/images", response_model=list[ProductImageResponse]
)
async def list_product_images(product_id: str, empresa_id: EmpresaId):
    """Lista as imagens de um produto, ordenadas por `position`."""
    await product_service.get_product(empresa_id, product_id)
    return await product_image_service.list_product_images(empresa_id, product_id)


@router.post(
    "/products/{product_id}/images",
    response_model=ProductImageResponse,
    status_code=201,
)
async def attach_product_image(
    product_id: str, data: CreateProductImageRequest, empresa_id: EmpresaId
):
    """Anexa uma imagem (URL pública) a um produto."""
    await product_service.get_product(empresa_id, product_id)
    return await product_image_service.attach_product_image(
        empresa_id, product_id, url=data.url, position=data.position
    )


@router.delete(
    "/products/{product_id}/images/{image_id}", response_model=SuccessResponse
)
async def delete_product_image(
    product_id: str, image_id: str, empresa_id: EmpresaId
):
    """Remove uma imagem do produto (também apaga do storage quando aplicável)."""
    await product_service.get_product(empresa_id, product_id)
    await product_image_service.delete_product_image(empresa_id, image_id)
    return SuccessResponse(message="Imagem removida com sucesso")


@router.post(
    "/products/{product_id}/images/reorder",
    response_model=list[ProductImageResponse],
)
async def reorder_product_images(
    product_id: str, data: ReorderImagesRequest, empresa_id: EmpresaId
):
    """Reordena as imagens de um produto pela ordem dos IDs informados."""
    await product_service.get_product(empresa_id, product_id)
    return await product_image_service.reorder_product_images(
        empresa_id, product_id, data.image_ids
    )


# =====================================================
# Categorias
# =====================================================


@router.get(
    "/product-categories", response_model=list[ProductCategoryResponse]
)
async def list_product_categories(empresa_id: EmpresaId):
    """Lista todas as categorias de produtos/serviços da empresa."""
    return await product_category_service.list_categories(empresa_id)


@router.get(
    "/product-categories/{category_id}", response_model=ProductCategoryResponse
)
async def get_product_category(category_id: str, empresa_id: EmpresaId):
    """Busca uma categoria por ID."""
    return await product_category_service.get_category(empresa_id, category_id)


@router.post(
    "/product-categories",
    response_model=ProductCategoryResponse,
    status_code=201,
)
async def create_product_category(
    data: CreateCategoryRequest, empresa_id: EmpresaId
):
    """Cria uma nova categoria de produtos/serviços."""
    return await product_category_service.create_category(
        empresa_id, data.model_dump(exclude_none=True)
    )


@router.patch(
    "/product-categories/{category_id}", response_model=ProductCategoryResponse
)
async def update_product_category(
    category_id: str, data: UpdateCategoryRequest, empresa_id: EmpresaId
):
    """Atualiza parcialmente uma categoria."""
    return await product_category_service.update_category(
        empresa_id, category_id, data.model_dump(exclude_unset=True)
    )


@router.delete(
    "/product-categories/{category_id}", response_model=SuccessResponse
)
async def delete_product_category(category_id: str, empresa_id: EmpresaId):
    """Deleta uma categoria permanentemente."""
    await product_category_service.delete_category(empresa_id, category_id)
    return SuccessResponse(message="Categoria deletada com sucesso")
