from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routers.v1 import leads, pipelines, custom_fields, users, vehicles, tasks, bookings

DESCRIPTION = """
## API pública do Aucta CRM

Permite que desenvolvedores integrem seus sistemas com o CRM através de tokens de API.

### Autenticação

Todas as requisições exigem um token de API no header `Authorization`:

```
Authorization: Bearer adv_live_xxxxxxxxxxxxxxxx
```

Gere seu token no painel do CRM em **Configurações > Integrações > API Keys**.

### Recursos disponíveis

- **Leads** — Criar, listar, atualizar e gerenciar leads
- **Tarefas** — CRUD completo de tarefas, comentários e tipos
- **Pipelines** — Consultar pipelines e stages (somente leitura)
- **Veículos** — Consultar estoque de veículos com imagens
- **Campos Customizados** — Consultar definições e gerenciar valores
- **Agendamentos** — Agendas, tipos, disponibilidade e CRUD de bookings
- **Usuários** — Listar usuários da empresa (somente leitura)
"""

settings = get_settings()

app = FastAPI(
    title=settings.API_TITLE,
    description=DESCRIPTION,
    version=settings.API_VERSION,
    docs_url=None,   # Desabilitado — customizado abaixo
    redoc_url=None,  # Desabilitado — customizado abaixo
    openapi_url="/openapi.json",
)

# Arquivos estáticos (favicon)
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

FAVICON_URL = "/static/favicon.svg"


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.API_TITLE} — Docs",
        swagger_favicon_url=FAVICON_URL,
    )


@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{settings.API_TITLE} — ReDoc",
        redoc_favicon_url=FAVICON_URL,
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers v1
app.include_router(leads.router, prefix="/api/v1", tags=["Leads"])
app.include_router(pipelines.router, prefix="/api/v1", tags=["Pipelines"])
app.include_router(custom_fields.router, prefix="/api/v1", tags=["Campos Customizados"])
app.include_router(users.router, prefix="/api/v1", tags=["Usuários"])
app.include_router(vehicles.router, prefix="/api/v1", tags=["Veículos"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tarefas"])
app.include_router(bookings.router, prefix="/api/v1", tags=["Agendamentos"])


@app.get("/", include_in_schema=False)
async def root():
    """Redireciona para a documentação."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Sistema"])
async def health_check():
    """Verifica se a API está funcionando."""
    return {"status": "ok", "version": settings.API_VERSION}
