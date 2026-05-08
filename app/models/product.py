from typing import Literal

from pydantic import BaseModel, Field, model_validator

ProductStatus = Literal["ativo", "inativo", "esgotado", "vendido"]
ProductType = Literal["produto", "servico"]
RecurrenceType = Literal[
    "unico",
    "semanal",
    "quinzenal",
    "mensal",
    "bimestral",
    "trimestral",
    "semestral",
    "anual",
]
SortBy = Literal[
    "preco_asc",
    "preco_desc",
    "nome_asc",
    "nome_desc",
    "created_desc",
    "created_asc",
    "estoque_asc",
    "estoque_desc",
]
StatusProduto = Literal["ativo", "vendido", "todos"]


# =====================================================
# Response Models
# =====================================================


class ProductCategoryResponse(BaseModel):
    """Categoria de produto/serviço configurada na empresa."""

    id: str
    empresa_id: str
    nome: str
    descricao: str | None = None
    created_at: str


class ProductImageResponse(BaseModel):
    """Imagem associada a um produto/serviço."""

    id: str
    product_id: str
    empresa_id: str
    url: str
    position: int
    created_at: str


class ProductResponse(BaseModel):
    """Representação completa de um produto/serviço na resposta da API."""

    id: str
    empresa_id: str
    nome: str
    descricao: str | None = None
    sku: str | None = None
    categoria_id: str | None = None
    marca: str | None = None
    preco: float | None = None
    preco_promocional: float | None = None
    quantidade_estoque: int = 0
    unidade_medida: str = "un"
    status: ProductStatus
    tipo: ProductType
    duracao_estimada: str | None = None
    recorrencia: RecurrenceType | None = None
    created_at: str
    updated_at: str
    category: ProductCategoryResponse | None = None
    images: list[ProductImageResponse] = []


# =====================================================
# Request Models — Products
# =====================================================


class CreateProductRequest(BaseModel):
    """Dados para criação de um novo produto/serviço."""

    nome: str = Field(..., min_length=1, max_length=300, description="Nome do produto/serviço")
    descricao: str | None = Field(None, description="Descrição detalhada")
    sku: str | None = Field(None, description="Código SKU")
    categoria_id: str | None = Field(None, description="ID da categoria")
    marca: str | None = Field(None, description="Marca")
    preco: float | None = Field(None, ge=0, description="Preço de venda")
    preco_promocional: float | None = Field(None, ge=0, description="Preço promocional")
    quantidade_estoque: int = Field(0, ge=0, description="Quantidade em estoque")
    unidade_medida: str = Field("un", description="Unidade de medida (un, kg, h, etc.)")
    status: ProductStatus = Field("ativo", description="Status do item")
    tipo: ProductType = Field("produto", description="Tipo: produto ou servico")
    duracao_estimada: str | None = Field(None, description="Duração estimada (apenas serviços)")
    recorrencia: RecurrenceType | None = Field(None, description="Recorrência (apenas serviços)")


class UpdateProductRequest(BaseModel):
    """Dados para atualização parcial de um produto/serviço."""

    nome: str | None = Field(None, min_length=1, max_length=300)
    descricao: str | None = None
    sku: str | None = None
    categoria_id: str | None = None
    marca: str | None = None
    preco: float | None = Field(None, ge=0)
    preco_promocional: float | None = Field(None, ge=0)
    quantidade_estoque: int | None = Field(None, ge=0)
    unidade_medida: str | None = None
    status: ProductStatus | None = None
    tipo: ProductType | None = None
    duracao_estimada: str | None = None
    recorrencia: RecurrenceType | None = None


# =====================================================
# Request Models — Categories
# =====================================================


class CreateCategoryRequest(BaseModel):
    """Dados para criação de uma categoria de produtos/serviços."""

    nome: str = Field(..., min_length=1, max_length=200, description="Nome da categoria")
    descricao: str | None = Field(None, description="Descrição opcional")


class UpdateCategoryRequest(BaseModel):
    """Dados para atualização parcial de uma categoria."""

    nome: str | None = Field(None, min_length=1, max_length=200)
    descricao: str | None = None


# =====================================================
# Request Models — Images
# =====================================================


class CreateProductImageRequest(BaseModel):
    """Anexa uma imagem (já hospedada externamente) a um produto/serviço."""

    url: str = Field(..., min_length=1, description="URL pública da imagem")
    position: int = Field(0, ge=0, description="Posição da imagem na listagem (0 = primeira)")


class ReorderImagesRequest(BaseModel):
    """Reordena as imagens de um produto/serviço."""

    image_ids: list[str] = Field(
        ..., min_length=1, description="IDs das imagens na ordem desejada"
    )


# =====================================================
# Request Models — Ações especiais
# =====================================================


class MarkSoldRequest(BaseModel):
    """Marca um produto/serviço como vendido.

    Para serviços, `quantidade_vendida` é ignorada.
    Para produtos, decrementa o estoque pela quantidade informada.
    """

    quantidade_vendida: int = Field(1, ge=1, description="Quantidade vendida (default 1)")


class AdjustStockRequest(BaseModel):
    """Ajusta a quantidade em estoque de um produto.

    Forneça **apenas um** dos campos:
    - `delta`: incrementa (positivo) ou decrementa (negativo) o estoque atual.
    - `quantidade_estoque`: define o estoque para um valor absoluto.
    """

    delta: int | None = Field(None, description="Variação a aplicar no estoque")
    quantidade_estoque: int | None = Field(
        None, ge=0, description="Novo valor absoluto do estoque"
    )

    @model_validator(mode="after")
    def _validate_exclusive(self) -> "AdjustStockRequest":
        if self.delta is None and self.quantidade_estoque is None:
            raise ValueError(
                "Informe `delta` ou `quantidade_estoque` para ajustar o estoque."
            )
        if self.delta is not None and self.quantidade_estoque is not None:
            raise ValueError(
                "Informe apenas um entre `delta` e `quantidade_estoque`, não ambos."
            )
        return self
