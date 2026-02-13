from pydantic import BaseModel


class UserResponse(BaseModel):
    """Representação de um usuário da empresa (dados públicos apenas)."""

    uuid: str
    full_name: str
    email: str
    phone: str | None = None
