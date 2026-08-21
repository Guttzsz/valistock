from unittest.mock import MagicMock

from app.models.push_subscription import PushSubscription
from app.services import push_service
from tests.conftest import auth_headers, registrar_empresa

SUBSCRIPTION_PAYLOAD = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
    "keys": {"p256dh": "chave-p256dh-fake", "auth": "chave-auth-fake"},
}


def test_inscrever_salva_subscription(client, db_session):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.post("/api/push/inscrever", json=SUBSCRIPTION_PAYLOAD, headers=headers)
    assert resp.status_code == 204

    sub = db_session.query(PushSubscription).filter(PushSubscription.endpoint == SUBSCRIPTION_PAYLOAD["endpoint"]).first()
    assert sub is not None
    assert sub.p256dh == "chave-p256dh-fake"


def test_inscrever_duas_vezes_nao_duplica(client, db_session):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    client.post("/api/push/inscrever", json=SUBSCRIPTION_PAYLOAD, headers=headers)
    client.post("/api/push/inscrever", json=SUBSCRIPTION_PAYLOAD, headers=headers)

    total = db_session.query(PushSubscription).filter(PushSubscription.endpoint == SUBSCRIPTION_PAYLOAD["endpoint"]).count()
    assert total == 1


def test_desinscrever_remove(client, db_session):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    client.post("/api/push/inscrever", json=SUBSCRIPTION_PAYLOAD, headers=headers)
    resp = client.request("DELETE", "/api/push/inscrever", json={"endpoint": SUBSCRIPTION_PAYLOAD["endpoint"]}, headers=headers)
    assert resp.status_code == 204

    total = db_session.query(PushSubscription).filter(PushSubscription.endpoint == SUBSCRIPTION_PAYLOAD["endpoint"]).count()
    assert total == 0


def test_criar_produto_com_lote_vencido_dispara_push(client, db_session, monkeypatch):
    """Regressao: criar um alerta novo (nao duplicado) deve chamar o envio de push."""
    from datetime import timedelta

    from app.utils.timezone import today

    monkeypatch.setattr(push_service.settings, "vapid_private_key", "chave-fake-para-teste")
    monkeypatch.setattr(push_service.settings, "vapid_public_key", "chave-publica-fake")
    monkeypatch.setattr(push_service.settings, "vapid_admin_email", "test@example.com")

    webpush_mock = MagicMock()
    monkeypatch.setattr(push_service, "webpush", webpush_mock)

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    empresa_id = data["usuario"]["empresa_id"]

    client.post("/api/push/inscrever", json=SUBSCRIPTION_PAYLOAD, headers=headers)

    produto_resp = client.post(
        "/api/produtos", json={"nome": "Iogurte", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers
    )
    produto_id = produto_resp.json()["id"]

    client.post(
        "/api/lotes",
        json={"produto_id": produto_id, "quantidade": 5, "data_validade": str(today() - timedelta(days=1))},
        headers=headers,
    )

    from app.services.alerta_service import verificar_vencimentos_empresa

    verificar_vencimentos_empresa(db_session, empresa_id)

    assert webpush_mock.called


def test_push_nao_configurado_nao_quebra(db_session, monkeypatch):
    """Sem VAPID configurado (ex.: ambiente sem push habilitado), enviar_push_para_empresa nao deve levantar erro."""
    monkeypatch.setattr(push_service.settings, "vapid_private_key", "")
    push_service.enviar_push_para_empresa(db_session, "00000000-0000-0000-0000-000000000000", "titulo", "corpo")
