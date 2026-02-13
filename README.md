# ADV-CRM API

API pública do ADV-CRM para integrações de terceiros. Construída com FastAPI + Supabase.

## Requisitos

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) (gerenciador de pacotes)

## Setup Local

```bash
# Instalar UV (se ainda não tem)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependências
cd api_crm
uv sync

# Copiar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais do Supabase

# Rodar o servidor
uv run uvicorn app.main:app --reload --port 8000
```

Acesse a documentação interativa em: [http://localhost:8000/docs](http://localhost:8000/docs)

## Migration do Banco

Antes de usar a API, execute a migration `migration_api_tokens.sql` no Supabase Dashboard (SQL Editor) para criar a tabela de tokens.

## Autenticação

Todas as requisições exigem um token de API no header:

```
Authorization: Bearer adv_live_xxxxxxxxxxxxxxxx
```

Tokens são gerados no painel do CRM em **Configurações > Integrações > API Keys**.

## Endpoints Disponíveis

### Leads
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/leads` | Listar leads (paginado + filtros) |
| GET | `/api/v1/leads/{id}` | Buscar lead por ID |
| POST | `/api/v1/leads` | Criar lead |
| PATCH | `/api/v1/leads/{id}` | Atualizar lead |
| DELETE | `/api/v1/leads/{id}` | Deletar lead |
| PATCH | `/api/v1/leads/{id}/stage` | Mover de stage |
| POST | `/api/v1/leads/{id}/mark-lost` | Marcar como perdido |
| POST | `/api/v1/leads/{id}/mark-sold` | Marcar como vendido |
| POST | `/api/v1/leads/{id}/reactivate` | Reativar lead |
| GET | `/api/v1/leads/{id}/history` | Histórico do lead |
| GET | `/api/v1/leads/tags` | Listar tags |
| GET | `/api/v1/leads/origins` | Listar origens |

### Pipelines (somente leitura)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/pipelines` | Listar pipelines |
| GET | `/api/v1/pipelines/{id}` | Pipeline por ID (com stages) |
| GET | `/api/v1/pipelines/{id}/stages` | Stages de um pipeline |

### Campos Customizados
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/custom-fields` | Listar definições |
| GET | `/api/v1/leads/{id}/custom-values` | Valores de um lead |
| PUT | `/api/v1/leads/{id}/custom-values` | Setar valores |

### Usuários (somente leitura)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/users` | Listar usuários da empresa |

### Sistema
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |

## Deploy com Docker (EasyPanel/Hostinger)

### Build e Run

```bash
docker build -t api-crm .
docker run -p 8000:8000 --env-file .env api-crm
```

### Configuração no EasyPanel

1. Criar novo serviço do tipo **Docker**
2. Conectar ao repositório Git ou fazer upload da imagem
3. Configurar variáveis de ambiente:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `API_ENV=production`
   - `ALLOWED_ORIGINS=https://app.advcrm.com.br`
4. Porta: `8000`
5. Configurar domínio/subdomínio (ex: `api.advcrm.com.br`)
6. Ativar HTTPS

## Estrutura do Projeto

```
api_crm/
├── app/
│   ├── main.py              # Entry point FastAPI
│   ├── core/
│   │   ├── config.py        # Settings (env vars)
│   │   ├── security.py      # Validação de API tokens
│   │   ├── dependencies.py  # FastAPI Depends
│   │   └── exceptions.py    # Exceções HTTP
│   ├── models/              # Pydantic schemas
│   ├── routers/v1/          # Endpoints por domínio
│   ├── services/            # Lógica de negócio
│   └── utils/               # Supabase client, paginação
├── pyproject.toml           # UV config + deps
├── Dockerfile
└── .env.example
```
