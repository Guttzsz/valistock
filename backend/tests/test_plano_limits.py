import pytest

from app.services.plano_service import LIMITES, check_plan_limit
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
