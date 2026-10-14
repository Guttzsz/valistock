from types import SimpleNamespace

from app.models.subscription import PlanoNome
from app.services import stripe_service
from app.services.plano_service import LIMITES
from tests.conftest import auth_headers, registrar_empresa


def test_checkout_cria_sessao_stripe(client, monkeypatch):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    monkeypatch.setattr(stripe_service.stripe.Customer, "create", lambda **kw: SimpleNamespace(id="cus_fake_123"))
    monkeypatch.setattr(
        stripe_service.stripe.checkout.Session, "create", lambda **kw: SimpleNamespace(url="https://checkout.stripe.com/fake")
    )

    resp = client.post("/api/subscriptions/checkout", json={"plano": "essencial"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["url"] == "https://checkout.stripe.com/fake"


def test_checkout_reusa_customer_existente(client, monkeypatch, db_session):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    chamadas_customer = []
    monkeypatch.setattr(
        stripe_service.stripe.Customer,
        "create",
        lambda **kw: chamadas_customer.append(1) or SimpleNamespace(id="cus_fake_456"),
    )
    monkeypatch.setattr(
        stripe_service.stripe.checkout.Session, "create", lambda **kw: SimpleNamespace(url="https://checkout.stripe.com/fake")
    )

    client.post("/api/subscriptions/checkout", json={"plano": "essencial"}, headers=headers)
    client.post("/api/subscriptions/checkout", json={"plano": "profissional"}, headers=headers)

    assert len(chamadas_customer) == 1


def test_checkout_com_plano_invalido_falha(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.post("/api/subscriptions/checkout", json={"plano": "inexistente"}, headers=headers)
    assert resp.status_code == 422


def test_funcionario_nao_pode_criar_checkout(client, monkeypatch):
    monkeypatch.setitem(LIMITES[PlanoNome.GRATUITO], "users", 5)
    data = registrar_empresa(client, "a")
    headers_admin = auth_headers(data["access_token"])
    client.post(
        "/api/usuarios",
        json={"nome": "Func", "email": "func_checkout@example.com", "senha": "SenhaForte123!", "perfil": "funcionario"},
        headers=headers_admin,
    )
    login = client.post("/api/auth/login", json={"email": "func_checkout@example.com", "senha": "SenhaForte123!"}).json()
    headers_func = auth_headers(login["access_token"])

    resp = client.post("/api/subscriptions/checkout", json={"plano": "essencial"}, headers=headers_func)
    assert resp.status_code == 403


def test_portal_sem_assinatura_stripe_falha(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.post("/api/subscriptions/portal", headers=headers)
    assert resp.status_code == 422


def test_portal_com_customer_existente_funciona(client, monkeypatch, db_session):
    from app.models.subscription import Subscription

    data = registrar_empresa(client, "a")
    empresa_id = data["usuario"]["empresa_id"]
    headers = auth_headers(data["access_token"])

    sub = Subscription(empresa_id=empresa_id, stripe_customer_id="cus_existente")
    db_session.add(sub)
    db_session.commit()

    monkeypatch.setattr(
        stripe_service.stripe.billing_portal.Session, "create", lambda **kw: SimpleNamespace(url="https://billing.stripe.com/fake")
    )

    resp = client.post("/api/subscriptions/portal", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["url"] == "https://billing.stripe.com/fake"


def test_portal_com_erro_do_stripe_retorna_mensagem_amigavel(client, monkeypatch, db_session):
    from app.models.subscription import Subscription

    data = registrar_empresa(client, "a")
    empresa_id = data["usuario"]["empresa_id"]
    headers = auth_headers(data["access_token"])

    sub = Subscription(empresa_id=empresa_id, stripe_customer_id="cus_existente")
    db_session.add(sub)
    db_session.commit()

    def _levanta_erro(**kw):
        raise stripe_service.stripe.InvalidRequestError("No configuration provided", param=None)

    monkeypatch.setattr(stripe_service.stripe.billing_portal.Session, "create", _levanta_erro)

    resp = client.post("/api/subscriptions/portal", headers=headers)
    assert resp.status_code == 422
    assert "No configuration provided" not in resp.json()["detail"]


def test_cancelar_assinatura_marca_cancelamento_no_fim_do_periodo(client, monkeypatch, db_session):
    from app.models.subscription import Subscription

    data = registrar_empresa(client, "a")
    empresa_id = data["usuario"]["empresa_id"]
    headers = auth_headers(data["access_token"])

    sub = Subscription(empresa_id=empresa_id, stripe_customer_id="cus_existente", stripe_subscription_id="sub_existente")
    db_session.add(sub)
    db_session.commit()

    def _modify(subscription_id, **kw):
        assert subscription_id == "sub_existente"
        assert kw["cancel_at_period_end"] is True
        # O SDK real devolve um StripeObject (sem .get()), nao um dict: o teste precisa refletir isso.
        return stripe_service.stripe.Subscription.construct_from(
            {
                "id": "sub_existente",
                "customer": "cus_existente",
                "status": "active",
                "cancel_at_period_end": True,
                "metadata": {"empresa_id": empresa_id},
                "items": {"data": []},
            },
            "sk_test",
        )

    monkeypatch.setattr(stripe_service.stripe.Subscription, "modify", _modify)

    resp = client.post("/api/subscriptions/cancelar", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["cancelar_ao_fim_periodo"] is True


def test_reativar_assinatura_desfaz_cancelamento(client, monkeypatch, db_session):
    from app.models.subscription import Subscription

    data = registrar_empresa(client, "a")
    empresa_id = data["usuario"]["empresa_id"]
    headers = auth_headers(data["access_token"])

    sub = Subscription(
        empresa_id=empresa_id, stripe_customer_id="cus_existente", stripe_subscription_id="sub_existente", cancelar_ao_fim_periodo=True
    )
    db_session.add(sub)
    db_session.commit()

    def _modify(subscription_id, **kw):
        assert kw["cancel_at_period_end"] is False
        # O SDK real devolve um StripeObject (sem .get()), nao um dict: o teste precisa refletir isso.
        return stripe_service.stripe.Subscription.construct_from(
            {
                "id": "sub_existente",
                "customer": "cus_existente",
                "status": "active",
                "cancel_at_period_end": False,
                "metadata": {"empresa_id": empresa_id},
                "items": {"data": []},
            },
            "sk_test",
        )

    monkeypatch.setattr(stripe_service.stripe.Subscription, "modify", _modify)

    resp = client.post("/api/subscriptions/reativar", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["cancelar_ao_fim_periodo"] is False


def test_cancelar_sem_assinatura_stripe_falha(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.post("/api/subscriptions/cancelar", headers=headers)
    assert resp.status_code == 422


def test_funcionario_nao_pode_cancelar_assinatura(client, monkeypatch):
    monkeypatch.setitem(LIMITES[PlanoNome.GRATUITO], "users", 5)
    data = registrar_empresa(client, "a")
    headers_admin = auth_headers(data["access_token"])
    client.post(
        "/api/usuarios",
        json={"nome": "Func", "email": "func_cancelar@example.com", "senha": "SenhaForte123!", "perfil": "funcionario"},
        headers=headers_admin,
    )
    login = client.post("/api/auth/login", json={"email": "func_cancelar@example.com", "senha": "SenhaForte123!"}).json()
    headers_func = auth_headers(login["access_token"])

    resp = client.post("/api/subscriptions/cancelar", headers=headers_func)
    assert resp.status_code == 403


def test_checkout_com_erro_do_stripe_responde_502_com_cors(client, monkeypatch):
    data = registrar_empresa(client, "a")
    headers = {**auth_headers(data["access_token"]), "Origin": "https://valistock.vercel.app"}

    def _falhar(**kw):
        raise stripe_service.stripe.InvalidRequestError("No such price: 'price_x'", "line_items")

    monkeypatch.setattr(stripe_service.stripe.Customer, "create", lambda **kw: SimpleNamespace(id="cus_fake_789"))
    monkeypatch.setattr(stripe_service.stripe.checkout.Session, "create", _falhar)

    resp = client.post("/api/subscriptions/checkout", json={"plano": "essencial"}, headers=headers)
    assert resp.status_code == 502
    assert "access-control-allow-origin" in resp.headers


def test_sincronizar_busca_assinatura_do_customer_no_stripe(client, monkeypatch, db_session):
    from app.config import get_settings
    from app.models.subscription import Subscription

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    empresa_id = data["usuario"]["empresa_id"]

    monkeypatch.setattr(stripe_service.stripe.Customer, "create", lambda **kw: SimpleNamespace(id="cus_sync_1"))
    monkeypatch.setattr(stripe_service.stripe.checkout.Session, "create", lambda **kw: SimpleNamespace(url="https://checkout.stripe.com/fake"))
    client.post("/api/subscriptions/checkout", json={"plano": "essencial"}, headers=headers)

    stripe_sub = {
        "id": "sub_sync_1",
        "customer": "cus_sync_1",
        "status": "active",
        "metadata": {"empresa_id": empresa_id},
        "items": {"data": [{"price": {"id": get_settings().stripe_price_essencial, "unit_amount": 2990}}]},
        "cancel_at_period_end": False,
    }
    chamadas = []

    def _listar(**kw):
        chamadas.append(kw)
        return SimpleNamespace(data=[SimpleNamespace(to_dict=lambda: stripe_sub)])

    monkeypatch.setattr(stripe_service.stripe.Subscription, "list", _listar)

    resp = client.post("/api/subscriptions/sincronizar", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["plano"] == PlanoNome.ESSENCIAL.value
    assert chamadas[0]["customer"] == "cus_sync_1"
    db_session.expire_all()
    assert db_session.query(Subscription).filter_by(stripe_customer_id="cus_sync_1").one().stripe_subscription_id == "sub_sync_1"


def test_sincronizar_sem_customer_nao_chama_stripe(client, monkeypatch):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    def _nao_deveria_chamar(**kw):
        raise AssertionError("nao deveria consultar o Stripe sem customer")

    monkeypatch.setattr(stripe_service.stripe.Subscription, "list", _nao_deveria_chamar)
    resp = client.post("/api/subscriptions/sincronizar", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["plano"] == PlanoNome.GRATUITO.value
