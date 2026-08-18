import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app.database import Base, get_db
from app.main import app

# O agendador de verificacao diaria nao deve rodar durante os testes: ele usaria
# a engine de producao (sem tabelas neste processo) e criaria uma thread em segundo
# plano por teste. A logica do servico em si e coberta por tests/test_alertas.py.
main_module.start_scheduler = lambda: None
main_module.stop_scheduler = lambda scheduler: None

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def registrar_empresa(client, sufixo="a"):
    payload = {
        "empresa_nome_fantasia": f"Mercado {sufixo}",
        "empresa_email": f"mercado{sufixo}@example.com",
        "admin_nome": f"Admin {sufixo}",
        "admin_email": f"admin{sufixo}@example.com",
        "admin_senha": "SenhaForte123!",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
