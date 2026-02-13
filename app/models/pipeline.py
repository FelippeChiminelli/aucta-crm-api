from pydantic import BaseModel


class StageResponse(BaseModel):
    """Representação de um Stage (etapa) do pipeline."""

    id: str
    pipeline_id: str
    name: str
    color: str
    position: int
    is_inicial: bool | None = None
    created_at: str


class PipelineResponse(BaseModel):
    """Representação de um Pipeline na resposta da API."""

    id: str
    name: str
    description: str | None = None
    active: bool
    display_order: int | None = None
    created_at: str
    # Stages opcionalmente populados
    stages: list[StageResponse] | None = None
