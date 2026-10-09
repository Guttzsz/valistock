# ValiStock

**Menos perdas. Mais lucro.**

SaaS de controle de validade e perdas para pequenos mercados, hortifrutis, padarias e quitandas. O funcionario cadastra produtos e lotes, informa a validade, e o sistema acompanha automaticamente os vencimentos, gerando alertas antes que o produto vire prejuizo.

O repositorio ja passou por duas fases:

- **Fase 1 (MVP)**: autenticacao, multi-tenancy, produtos, lotes, validades, alertas automaticos, controle de perdas, dashboard, relatorios com graficos.
- **Fase 2 (plataforma configuravel)**: categorias/fornecedores/localizacoes como entidades reais da empresa, permissoes granulares por perfil, auditoria (historico de acoes), rastreabilidade de movimentacao de estoque, campos personalizados por produto, onboarding guiado, preferencias de notificacao/dashboard por usuario, exportacao CSV.

Codigo de barras (camera), OCR de validade e Stripe checkout estao com a arquitetura preparada mas as integracoes completas ficam para as proximas fases (veja [Roadmap](#roadmap)).

**Esta em producao real:** frontend na Vercel, backend no Render, banco no Supabase — nao e so uma demonstracao local.

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
│   │   ├── models/        # SQLAlchemy ORM (Empresa, Usuario, Produto, Lote, Perda, Alerta,
│   │   │                  #   Categoria, Fornecedor, Localizacao, CampoPersonalizado,
│   │   │                  #   LogAuditoria, MovimentacaoEstoque, Preferencia*, ...)
│   │   ├── schemas/       # Pydantic (request/response)
│   │   ├── routes/        # Endpoints FastAPI, um arquivo por recurso
│   │   ├── services/      # Regras de negocio (validade, alertas, financeiro, planos, estoque,
│   │   │                  #   auditoria, scheduler)
│   │   ├── auth/          # Hash de senha, JWT, dependencias de autenticacao/autorizacao,
│   │   │                  #   matriz de permissoes granulares (permissions.py)
│   │   ├── utils/         # Timezone, excecoes amigaveis, tipo GUID multi-banco
│   │   ├── config.py      # Configuracao via variaveis de ambiente (pydantic-settings)
│   │   ├── database.py    # Engine/Session do SQLAlchemy
│   │   └── main.py        # App FastAPI, CORS, rotas, lifespan (scheduler)
│   ├── migrations/        # Alembic
│   ├── tests/              # pytest (70 testes cobrindo auth, multi-tenancy, regras de negocio)
│   ├── seed.py             # Popula o banco com a empresa de demonstracao
│   ├── run.py               # Entry point local (uvicorn)
│   ├── requirements.txt
│   ├── requirements-dev.txt
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
pip install -r requirements-dev.txt   # requirements.txt + dependencias de teste

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

70 testes, sem dependencia de um Postgres rodando (usam SQLite em memoria via um tipo `GUID` que e nativo em Postgres e compativel em SQLite). Cobrem:

- cadastro, login, hash de senha, protecao de rotas, troca de senha/perfil;
- CRUD de produtos e lotes, atualizacao automatica de estoque;
- calculo de dias restantes e status de validade (normal/atencao/urgente/vence hoje/vencido);
- geracao de alertas (7/3/1 dias, vence hoje, vencido, estoque baixo) e nao duplicacao;
- registro de perdas e calculo financeiro (quantidade × custo);
- CRUD de categorias, fornecedores, localizacoes e campos personalizados;
- auditoria (logs_auditoria) e rastreabilidade de estoque (movimentacoes_estoque);
- onboarding e preferencias (notificacao/dashboard) persistidos no banco;
- **isolamento entre empresas** (uma empresa nunca ve dados de outra) — o requisito de seguranca mais critico do produto, testado explicitamente para cada entidade nova;
- permissoes granulares por perfil (administrador/gerente/funcionario) via `app/auth/permissions.py`;
- limites de plano (`check_plan_limit`).

Rode `pytest` sempre depois de mudar um model relacionado a enums Postgres — o SQLite dos testes usa CHECK constraints geradas pelo SQLAlchemy a partir do mesmo enum Python, o que pode mascarar incompatibilidades reais com Postgres (ja aconteceu: veja o commit "Fix enum name/value mismatch"). Para validar de verdade contra Postgres antes de um deploy sensivel, rode a suite ou um teste manual apontando `DATABASE_URL` para o Supabase.

## Endpoints da API

Todos exigem `Authorization: Bearer <token>`, exceto `/api/auth/register` e `/api/auth/login`.

```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me
PUT    /api/auth/perfil
PUT    /api/auth/senha
GET    /api/auth/permissoes                   (lista as permissoes do usuario logado; so cosmetico)

GET    /api/empresas/atual
PUT    /api/empresas/atual                    (empresa.gerenciar)

GET    /api/usuarios
POST   /api/usuarios                          (funcionarios.gerenciar)
PUT    /api/usuarios/{id}                     (funcionarios.gerenciar)
DELETE /api/usuarios/{id}                     (funcionarios.gerenciar)

GET    /api/produtos?q=&categoria_id=&fornecedor_id=&localizacao_id=
POST   /api/produtos
GET    /api/produtos/{id}
PUT    /api/produtos/{id}
DELETE /api/produtos/{id}
GET    /api/produtos/buscar/codigo-barras/{codigo}
GET    /api/produtos/{id}/campos-personalizados
PUT    /api/produtos/{id}/campos-personalizados

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

GET    /api/categorias?q=&incluir_inativas=
POST   /api/categorias                        (categorias.gerenciar)
PUT    /api/categorias/{id}                   (categorias.gerenciar)
DELETE /api/categorias/{id}                   (categorias.gerenciar; desativa, nao apaga)

GET    /api/fornecedores?q=&incluir_inativos=
POST   /api/fornecedores                      (fornecedores.gerenciar)
PUT    /api/fornecedores/{id}                 (fornecedores.gerenciar)
DELETE /api/fornecedores/{id}                 (fornecedores.gerenciar)

GET    /api/localizacoes
POST   /api/localizacoes                      (localizacoes.gerenciar)
PUT    /api/localizacoes/{id}                 (localizacoes.gerenciar)
DELETE /api/localizacoes/{id}                 (localizacoes.gerenciar)

GET    /api/campos-personalizados
POST   /api/campos-personalizados             (configuracoes.gerenciar)
PUT    /api/campos-personalizados/{id}        (configuracoes.gerenciar)
DELETE /api/campos-personalizados/{id}        (configuracoes.gerenciar)

GET    /api/historico?usuario_id=&acao=&entidade=&data_inicio=&data_fim=   (auditoria.visualizar)
GET    /api/historico/estoque?produto_id=                                   (auditoria.visualizar)

GET    /api/preferencias/notificacoes
PUT    /api/preferencias/notificacoes
GET    /api/preferencias/dashboard
PUT    /api/preferencias/dashboard

GET    /api/dashboard

GET    /api/relatorios/perdas?periodo=hoje|7dias|30dias|90dias|personalizado
GET    /api/relatorios/perdas/exportar?periodo=      (CSV; relatorios.exportar)
GET    /api/relatorios/risco

GET    /api/configuracoes
PUT    /api/configuracoes/alertas             (configuracoes.gerenciar)
PUT    /api/configuracoes/empresa             (configuracoes.gerenciar)
PUT    /api/configuracoes/onboarding          (admin; avanca o fluxo guiado, persiste a cada etapa)

GET    /api/subscriptions/atual
```

## Multi-tenancy e seguranca

- Toda tabela de dados de negocio tem `empresa_id`. Todo endpoint filtra por `current_user.empresa_id`, extraido do JWT no backend — **nunca** de um parametro vindo do cliente. Ao criar/editar um produto com `categoria_id`/`fornecedor_id`/`localizacao_id`, o backend confirma que a referencia pertence a mesma empresa antes de aceitar (evita um usuario "colar" o id de uma categoria de outra empresa).
- Senhas com hash `bcrypt`, nunca armazenadas em texto puro. Troca de senha exige a senha atual.
- **Permissoes granulares por perfil**, nao apenas 3 niveis fixos: uma matriz centralizada em `app/auth/permissions.py` (`PERMISSOES_POR_PERFIL`) mapeia cada perfil (administrador/gerente/funcionario) para um conjunto de permissoes especificas (`produtos.criar`, `categorias.gerenciar`, `auditoria.visualizar`, etc.). Cada rota declara a permissao que exige via `require_permissao(...)`. O frontend consulta `GET /api/auth/permissoes` so para decidir o que mostrar/esconder na interface — a autorizacao real e **sempre** verificada de novo no backend, em cada request.
- Toda mutacao relevante (produto, lote, perda, categoria, fornecedor, localizacao, usuario, empresa, configuracao) grava um registro em `logs_auditoria` na mesma transacao — nunca depois, nunca best-effort.
- Toda alteracao de `produtos.estoque_atual` passa por `app/services/estoque_service.py::ajustar_estoque`, que tambem grava uma linha em `movimentacoes_estoque`. Nao existe um caminho no codigo que altere o estoque silenciosamente.
- Erros internos nunca vazam stack trace ao usuario (handler global retorna mensagem generica e loga o erro no servidor).
- Limites de plano centralizados em `app/services/plano_service.py` (`check_plan_limit`), evitando regra de negocio espalhada pelo codigo.
- `SUPABASE_SERVICE_ROLE_KEY` e as chaves do Stripe existem apenas no backend.

## Deploy

Instancia atual em producao:

| Camada | Onde | URL |
|---|---|---|
| Frontend | Vercel | https://valistock.vercel.app |
| Backend | Render | https://valistock-backend.onrender.com |
| Banco | Supabase (Postgres) | projeto `hgaapjgzjapeuxtrydnp` |

Passo a passo para replicar (ou migrar de provedor):

1. **Banco**: crie um projeto no Supabase, copie a `DATABASE_URL` no modo **Session pooler** (a conexao direta e IPv6-only e falha a partir da maioria dos PaaS, que so tem saida IPv4) e rode `alembic upgrade head` apontando para ela.
2. **Backend**: use o `render.yaml` incluido (Render Blueprint) ou o `Dockerfile` em qualquer servico Python (Railway/Fly.io/VPS). Configure as variaveis de `.env.example` no painel do servico — `DATABASE_URL` e `SECRET_KEY` como secrets.
3. **Frontend**: aponte um projeto Vercel para a pasta `frontend/`. Ajuste `VALISTOCK_API_BASE_URL` em `frontend/static/js/config.js` para a URL do backend em producao antes do deploy. Confira **Settings → Deployment Protection** esta desativado para producao, senao o site fica inacessivel para visitantes.
4. Configure `FRONTEND_URL` no backend (usado no CORS em producao) com a URL final da Vercel.
5. Rode uma migration nova (`alembic upgrade head`) manualmente contra o Supabase antes de fazer deploy de um backend que a exija — o deploy do backend em si nao roda migrations automaticamente hoje.

## Roadmap

- **Fase 3 (em andamento)**: leitura de codigo de barras via camera, OCR de validade, promocoes.
- **Fase 4**: Stripe Checkout, Customer Portal, webhooks de assinatura.
- **Fase 5**: notificacoes push/e-mail (hoje as preferencias ja existem no banco, falta o canal de envio), inteligencia preditiva de perdas, integracoes com ERP/PDV, app mobile nativo, RBAC totalmente dinamico (papeis customizados por empresa, hoje e uma matriz fixa por perfil), personalizacao visual completa (upload de logo via Supabase Storage), busca global, paginacao nas listagens.

A tabela `subscriptions` e os limites por plano (`app/services/plano_service.py`) ja existem e retornam plano "gratuito" por padrao; falta apenas o checkout e os webhooks do Stripe para ativar a cobranca.
