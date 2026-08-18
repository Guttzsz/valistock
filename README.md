# ValiStock

**Menos perdas. Mais lucro.**

SaaS de controle de validade e perdas para pequenos mercados, hortifrutis, padarias e quitandas. O funcionario cadastra produtos e lotes, informa a validade, e o sistema acompanha automaticamente os vencimentos, gerando alertas antes que o produto vire prejuizo.

Este repositorio contem a **Fase 1 (MVP)**: autenticacao, multi-tenancy, produtos, lotes, validades, alertas automaticos, controle de perdas, dashboard, relatorios com graficos e testes automatizados. Codigo de barras (camera), OCR de validade e Stripe estao com a arquitetura preparada mas as integracoes completas ficam para as proximas fases (veja [Roadmap](#roadmap)).

## Indice

- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Configuracao](#configuracao)
- [Rodando localmente](#rodando-localmente)
- [Rodando com Docker](#rodando-com-docker)
- [Migrations](#migrations)
- [Dados de demonstracao (seed)](#dados-de-demonstracao-seed)
- [Testes](#testes)
- [Endpoints da API](#endpoints-da-api)
- [Multi-tenancy e seguranca](#multi-tenancy-e-seguranca)
- [Deploy](#deploy)
- [Roadmap](#roadmap)

## Arquitetura

```
Frontend (HTML + CSS + JS, Bootstrap 5 + Chart.js)
        |
        v
   Vercel (estatico)
        |
        v  fetch() com JWT
Backend (Python + FastAPI + SQLAlchemy + Alembic)
        |
        v
PostgreSQL (Supabase em producao / Docker em dev)
        |
        v (Fase 3)
     Stripe
```

**Decisao tecnica: backend Python nao vai para a Vercel.** A Vercel roda Python apenas como funcoes serverless de vida curta, o que nao se encaixa bem com um servidor FastAPI com pool de conexoes de banco e um scheduler em background (verificacao diaria de vencimentos via APScheduler). Por isso:

- **Frontend** (estatico) → **Vercel**.
- **Backend** (FastAPI) → qualquer servico compativel com Python de longa duracao (Railway, Render, Fly.io, um VPS com Docker, etc). O `Dockerfile` e o `docker-compose.yml` deste repositorio funcionam em qualquer um desses.
- **Banco** → Supabase (PostgreSQL gerenciado) em producao; PostgreSQL local via Docker em desenvolvimento.
- **Pagamentos** → Stripe (Fase 3).

O frontend fala com o backend exclusivamente via REST + JWT (`Authorization: Bearer <token>`), sem nenhum acoplamento a framework — pode ser hospedado em qualquer CDN estatica.

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic |
| Autenticacao | JWT (python-jose) + bcrypt |
| Banco | PostgreSQL (Supabase em producao) |
| Agendador | APScheduler (verificacao diaria de vencimentos) |
| Frontend | HTML5, CSS3, JavaScript vanilla, Bootstrap 5, Chart.js |
| Pagamentos | Stripe (Fase 3) |
| Testes | pytest, httpx, SQLite em memoria |
| Deploy | Vercel (frontend) + Docker (backend) + Supabase (banco) |

## Estrutura do projeto

```
valistock/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy ORM (Empresa, Usuario, Produto, Lote, Perda, Alerta, ...)
│   │   ├── schemas/       # Pydantic (request/response)
│   │   ├── routes/        # Endpoints FastAPI, um arquivo por recurso
│   │   ├── services/      # Regras de negocio (validade, alertas, financeiro, planos, scheduler)
│   │   ├── auth/          # Hash de senha, JWT, dependencias de autenticacao/autorizacao
│   │   ├── utils/         # Timezone, excecoes amigaveis, tipo GUID multi-banco
│   │   ├── config.py      # Configuracao via variaveis de ambiente (pydantic-settings)
│   │   ├── database.py    # Engine/Session do SQLAlchemy
│   │   └── main.py        # App FastAPI, CORS, rotas, lifespan (scheduler)
│   ├── migrations/        # Alembic
│   ├── tests/              # pytest (44 testes cobrindo auth, multi-tenancy, regras de negocio)
│   ├── seed.py             # Popula o banco com a empresa de demonstracao
│   ├── run.py               # Entry point local (uvicorn)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── templates/          # Uma pagina HTML por tela (login, dashboard, produtos, ...)
│   └── static/
│       ├── css/style.css   # Design system do ValiStock
│       └── js/             # api.js (cliente REST), nav.js, e um arquivo por pagina
├── docker-compose.yml       # Postgres local + backend
├── .env.example
└── README.md
```

## Configuracao

Copie `.env.example` para `.env` na raiz do projeto e preencha:

```
DATABASE_URL=postgresql+psycopg2://valistock:valistock@localhost:5432/valistock
SECRET_KEY=uma-string-longa-e-aleatoria
SUPABASE_URL=...
SUPABASE_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...   # nunca exponha esta chave no frontend
STRIPE_SECRET_KEY=...           # Fase 3
```

`SUPABASE_SERVICE_ROLE_KEY` e as chaves do Stripe ficam **exclusivamente no backend**. O frontend nunca as recebe.

## Rodando localmente

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux/Mac
pip install -r requirements.txt

# Com Postgres rodando (veja "Rodando com Docker" abaixo) e DATABASE_URL configurada:
alembic upgrade head
python seed.py                    # opcional: cria a empresa "Mercado Sao Joao" com dados de exemplo
python run.py                     # sobe em http://localhost:8000
```

A documentacao interativa (Swagger) fica em `http://localhost:8000/docs`.

### Frontend

O frontend e 100% estatico. Para rodar localmente:

```bash
cd frontend
python -m http.server 5500
```

Abra `http://localhost:5500/templates/login.html`. Por padrao (`static/js/config.js`) ele aponta para `http://localhost:8000`; ajuste `VALISTOCK_API_BASE_URL` la para apontar para o backend de producao ao fazer deploy.

## Rodando com Docker

```bash
docker-compose up
```

Isso sobe o PostgreSQL local e o backend (que roda `alembic upgrade head` automaticamente antes de iniciar). O frontend continua sendo servido separadamente (passo acima ou Vercel).

## Migrations

Gerenciadas com Alembic. Nunca crie tabelas manualmente.

```bash
cd backend
alembic upgrade head                        # aplica migrations
alembic revision --autogenerate -m "..."     # gera uma nova migration a partir dos models
```

## Dados de demonstracao (seed)

```bash
cd backend
python seed.py
```

Cria a empresa **Mercado Sao Joao** com 8 produtos (leite, iogurte, queijo, tomate, banana, pao, presunto, refrigerante), cada um com 4 lotes cobrindo os status normal/atencao/vence-hoje/vencido, e algumas perdas de exemplo.

Login de demonstracao:

| Perfil | Email | Senha |
|---|---|---|
| Administrador | admin@mercadosaojoao.com.br | Senha123! |
| Funcionario | funcionario@mercadosaojoao.com.br | Senha123! |

## Testes

```bash
cd backend
pytest
```

44 testes, sem dependencia de um Postgres rodando (usam SQLite em memoria via um tipo `GUID` que e nativo em Postgres e compativel em SQLite). Cobrem:

- cadastro, login, hash de senha, protecao de rotas;
- CRUD de produtos e lotes, atualizacao automatica de estoque;
- calculo de dias restantes e status de validade (normal/atencao/urgente/vence hoje/vencido);
- geracao de alertas (7/3/1 dias, vence hoje, vencido, estoque baixo) e nao duplicacao;
- registro de perdas e calculo financeiro (quantidade × custo);
- **isolamento entre empresas** (uma empresa nunca ve dados de outra) — o requisito de seguranca mais critico do produto;
- permissoes por perfil (administrador/gerente/funcionario);
- limites de plano (`check_plan_limit`).

## Endpoints da API

Todos exigem `Authorization: Bearer <token>`, exceto `/api/auth/register` e `/api/auth/login`.

```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

GET    /api/empresas/atual
PUT    /api/empresas/atual                    (admin)

GET    /api/usuarios
POST   /api/usuarios                          (admin)
PUT    /api/usuarios/{id}                     (admin)
DELETE /api/usuarios/{id}                     (admin)

GET    /api/produtos?q=&categoria=
POST   /api/produtos
GET    /api/produtos/{id}
PUT    /api/produtos/{id}
DELETE /api/produtos/{id}
GET    /api/produtos/buscar/codigo-barras/{codigo}

GET    /api/lotes?produto_id=
POST   /api/lotes
PUT    /api/lotes/{id}
DELETE /api/lotes/{id}
PUT    /api/lotes/{id}/marcar-vendido

GET    /api/validades?status=

GET    /api/alertas?lido=
PUT    /api/alertas/{id}/ler
PUT    /api/alertas/{id}/ignorar

GET    /api/perdas?data_inicio=&data_fim=&produto_id=&motivo=
POST   /api/perdas

GET    /api/dashboard

GET    /api/relatorios/perdas?periodo=hoje|7dias|30dias|90dias|personalizado
GET    /api/relatorios/risco

GET    /api/configuracoes
PUT    /api/configuracoes                     (admin)

GET    /api/subscriptions/atual
```

## Multi-tenancy e seguranca

- Toda tabela de dados de negocio tem `empresa_id`. Todo endpoint filtra por `current_user.empresa_id`, extraido do JWT no backend — **nunca** de um parametro vindo do cliente.
- Senhas com hash `bcrypt`, nunca armazenadas em texto puro.
- Autorizacao por perfil (`administrador`/`gerente`/`funcionario`) via dependencies do FastAPI (`require_admin`, `require_gerente_ou_admin`).
- Erros internos nunca vazam stack trace ao usuario (handler global retorna mensagem generica e loga o erro no servidor).
- Limites de plano centralizados em `app/services/plano_service.py` (`check_plan_limit`), evitando regra de negocio espalhada pelo codigo.
- `SUPABASE_SERVICE_ROLE_KEY` e as chaves do Stripe existem apenas no backend.

## Deploy

1. **Banco**: crie um projeto no Supabase, copie a `DATABASE_URL` (modo "connection pooling" para produção) e rode `alembic upgrade head` apontando para ela.
2. **Backend**: faça deploy do conteúdo de `backend/` num serviço Python (Railway/Render/Fly.io) usando o `Dockerfile` incluído. Configure as variáveis de `.env.example` no painel do serviço.
3. **Frontend**: aponte um projeto Vercel para a pasta `frontend/`. Ajuste `VALISTOCK_API_BASE_URL` em `frontend/static/js/config.js` para a URL do backend em produção antes do deploy.
4. Configure `FRONTEND_URL` no backend (usado no CORS em produção) com a URL final da Vercel.

## Roadmap

- **Fase 2**: leitura de código de barras via câmera, OCR de validade, promoções, gráficos adicionais.
- **Fase 3**: Stripe Checkout, Customer Portal, webhooks de assinatura.
- **Fase 4**: notificações push/e-mail, inteligência preditiva de perdas, integrações com ERP/PDV, app mobile nativo.

A tabela `subscriptions` e os limites por plano (`app/services/plano_service.py`) já existem e retornam plano "gratuito" por padrão; falta apenas o checkout e os webhooks do Stripe para ativar a cobrança.
