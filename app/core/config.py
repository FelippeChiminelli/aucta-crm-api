from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações da API carregadas de variáveis de ambiente."""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # API
    API_ENV: str = "production"
    API_TITLE: str = "Aucta CRM - API"
    API_VERSION: str = "1.0.0"

    # CORS
    ALLOWED_ORIGINS: str = "*"

    @property
    def cors_origins(self) -> list[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_dev(self) -> bool:
        return self.API_ENV == "development"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
