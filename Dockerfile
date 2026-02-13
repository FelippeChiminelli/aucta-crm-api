FROM python:3.12-slim AS base

# Instalar UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Instalar dependências primeiro (cache de layer)
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project

# Copiar código da aplicação
COPY app/ ./app/

# Expor porta
EXPOSE 8000

# Executar com uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
