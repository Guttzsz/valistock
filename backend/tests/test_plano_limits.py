import pytest

from app.models.subscription import PlanoNome, StatusAssinatura, Subscription
from app.services.plano_service import LIMITES, check_plan_limit, get_plano_atual
from app.utils.exceptions import PlanLimitError
from tests.conftest import auth_headers, registrar_empresa


def test_plano_gratuito_bloqueia_apos_limite_de_produtos(client, db_session, monkeypatch):
    from uuid import UUID

    monkeypatch.setitem(LIMITES[list(LIMITES.keys())[0]], "products", 2)

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    empresa_id = UUID(data["usuario"]["empresa_id"])

    for i in range(2):
        resp = client.post(
            "/api/produtos", json={"nome": f"Produto {i}", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers
        )
        assert resp.status_code == 201

    resp = client.post(
        "/api/produtos", json={"nome": "Produto extra", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers
    )
    assert resp.status_code == 402

    with pytest.raises(PlanLimitError):
        check_plan_limit(db_session, empresa_id, "products")


def test_assinatura_cancelada_volta_para_plano_gratuito(client, db_session):
    """Regressao: uma assinatura Stripe cancelada nao pode continuar concedendo os limites do plano pago."""
    from uuid import UUID

    data = registrar_empresa(client, "a")
    empresa_id = UUID(data["usuario"]["empresa_id"])

    sub = Subscription(empresa_id=empresa_id, plano=PlanoNome.ESSENCIAL, status=StatusAssinatura.CANCELED)
    db_session.add(sub)
    db_session.commit()

    assert get_plano_atual(db_session, empresa_id) == PlanoNome.GRATUITO


def test_assinatura_past_due_mantem_direito_ao_plano(client, db_session):
    """Past_due (falha de pagamento com nova tentativa automatica do Stripe) nao corta acesso imediatamente."""
    from uuid import UUID

    data = registrar_empresa(client, "a")
    empresa_id = UUID(data["usuario"]["empresa_id"])

    sub = Subscription(empresa_id=empresa_id, plano=PlanoNome.PROFISSIONAL, status=StatusAssinatura.PAST_DUE)
    db_session.add(sub)
    db_session.commit()

    assert get_plano_atual(db_session, empresa_id) == PlanoNome.PROFISSIONAL


def test_plano_gratuito_bloqueia_apos_1_usuario(client, db_session):
    """Regra nova: o plano Gratuito permite so 1 usuario (o admin que se cadastrou)."""
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.post(
        "/api/usuarios",
        json={"nome": "Func", "email": "func_limite@example.com", "senha": "SenhaForte123!", "perfil": "funcionario"},
        headers=headers,
    )
    assert resp.status_code == 402


def test_plano_empresa_produtos_ilimitados_mas_usuarios_limitados_a_25():
    limites = LIMITES[PlanoNome.EMPRESA]
    assert limites["products"] is None
    assert limites["users"] == 25
