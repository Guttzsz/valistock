import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routes import (
    alertas,
    auth,
    campos_personalizados,
    categorias,
    configuracoes,
    dashboard,
    empresas,
    fornecedores,
    historico,
    localizacoes,
    lotes,
    perdas,
    preferencias,
    produtos,
    relatorios,
    subscriptions,
    usuarios,
    validades,
)
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("valistock")

settings = get_settings()


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url] if settings.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/", tags=["health"])
def root():
    return {"service": "ValiStock API", "status": "ok"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
