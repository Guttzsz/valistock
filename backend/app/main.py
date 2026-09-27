import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
from app.rate_limit import limiter
from app.routes import (
    alertas,
    auth,
    campos_personalizados,
    categorias,
    configuracoes,
    dashboard,
    empresas,
    financeiro,
    fornecedores,
    historico,
    localizacoes,
    lotes,
    perdas,
    preferencias,
    produtos,
    push,
    relatorios,
    stripe_webhook,
    subscriptions,
    usuarios,
    validades,
)
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("valistock")

settings = get_settings()

if settings.is_production and settings.secret_key == "insecure-dev-key-change-me":
    raise RuntimeError("SECRET_KEY nao foi configurada em producao. Defina a variavel de ambiente SECRET_KEY antes de subir o servico.")

if settings.is_production and not settings.mfa_encryption_key:
    raise RuntimeError("MFA_ENCRYPTION_KEY nao foi configurada em producao. Defina a variavel de ambiente MFA_ENCRYPTION_KEY antes de subir o servico.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.scheduler = start_scheduler()
    yield
    stop_scheduler(app.state.scheduler)


app = FastAPI(
    title="ValiStock API",
    description="API do ValiStock - controle de validade e perdas para pequenos comercios.",
    version="1.0.0",
    lifespan=lifespan,
)

MAX_BODY_BYTES = 2 * 1024 * 1024  # 2MB: nenhuma rota aceita upload de arquivo hoje, JSON nao precisa de mais que isso

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["valistock-backend.onrender.com"] if settings.is_production else ["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url] if settings.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.middleware("http")
async def limitar_tamanho_do_corpo_middleware(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Corpo da requisicao muito grande."})
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Erro nao tratado em %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Ocorreu um erro interno. Tente novamente mais tarde."})


app.include_router(auth.router)
app.include_router(empresas.router)
app.include_router(usuarios.router)
app.include_router(produtos.router)
app.include_router(lotes.router)
app.include_router(validades.router)
app.include_router(alertas.router)
app.include_router(perdas.router)
app.include_router(dashboard.router)
app.include_router(relatorios.router)
app.include_router(configuracoes.router)
app.include_router(subscriptions.router)
app.include_router(categorias.router)
app.include_router(fornecedores.router)
app.include_router(localizacoes.router)
app.include_router(campos_personalizados.router)
app.include_router(historico.router)
app.include_router(preferencias.router)
app.include_router(push.router)
app.include_router(financeiro.router)
app.include_router(stripe_webhook.router)


@app.get("/", tags=["health"])
def root():
    return {"service": "ValiStock API", "status": "ok"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
