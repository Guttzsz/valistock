import os

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["MFA_ENCRYPTION_KEY"] = "3iNZlyY4iCezOd3TZ4kuetmPlEI0-upgIUx27aXxtcI="
os.environ["STRIPE_SECRET_KEY"] = "sk_test_fake_for_pytest"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_secret_for_pytest"
os.environ["STRIPE_PRICE_ESSENCIAL"] = "price_test_essencial"
os.environ["STRIPE_PRICE_PROFISSIONAL"] = "price_test_profissional"
os.environ["STRIPE_PRICE_EMPRESA"] = "price_test_empresa"

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


def tornar_super_admin(db_session, email: str) -> None:
    from app.models.usuario import Usuario

    usuario = db_session.query(Usuario).filter(Usuario.email == email).first()
    usuario.super_admin = True
    db_session.commit()


def assinar_webhook_stripe(payload: bytes, secret: str = "whsec_test_secret_for_pytest") -> str:
    """Gera uma assinatura Stripe-Signature valida, no mesmo formato que o Stripe usa de verdade,
    para testar a verificacao de assinatura do endpoint de webhook sem precisar de um servidor Stripe real."""
    import hashlib
    import hmac
    import time

    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload.decode()}"
    signature = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"
