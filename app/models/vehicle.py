from pydantic import BaseModel


class VehicleImageResponse(BaseModel):
    """Imagem de um veículo."""

    id: str
    url: str
    position: int


class VehicleResponse(BaseModel):
    """Representação de um veículo do estoque na resposta da API."""

    id: str
    external_id: int
    titulo_veiculo: str | None = None
    modelo_veiculo: str | None = None
    marca_veiculo: str | None = None
    ano_veiculo: int | None = None
    ano_fabric_veiculo: int | None = None
    color_veiculo: str | None = None
    price_veiculo: float | None = None
    promotion_price: float | None = None
    accessories_veiculo: str | None = None
    plate_veiculo: str | None = None
    quilometragem_veiculo: int | None = None
    cambio_veiculo: str | None = None
    combustivel_veiculo: str | None = None
    created_at: str
    updated_at: str
    images: list[VehicleImageResponse] = []
