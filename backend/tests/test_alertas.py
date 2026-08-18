from datetime import timedelta

from app.services.alerta_service import verificar_vencimentos_empresa
from app.utils.timezone import today
from tests.conftest import auth_headers, registrar_empresa


def _criar_produto_e_lote(client, headers, dias_validade, estoque_minimo=5, quantidade=10):
    produto = client.post(
        "/api/produtos",
        json={"nome": "Queijo", "preco_custo": "10.00", "preco_venda": "18.00", "estoque_minimo": estoque_minimo},
        headers=headers,
    ).json()
    lote = client.post(
        "/api/lotes",
        json={
            "produto_id": produto["id"],
            "numero_lote": "LT001",
            "quantidade": quantidade,
            "data_validade": str(today() + timedelta(days=dias_validade)),
            "custo_unitario": "10.00",
        },
        headers=headers,
    ).json()
    return produto, lote


def test_alerta_gerado_no_limite_de_7_dias(client, db_session):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto, lote = _criar_produto_e_lote(client, headers, dias_validade=7)

    from uuid import UUID

    verificar_vencimentos_empresa(db_session, UUID(data["usuario"]["empresa_id"]))

    resp = client.get("/api/alertas", headers=headers)
    tipos = [a["tipo"] for a in resp.json()]
    assert "vencimento_7_dias" in tipos


def test_alerta_vencido_gerado_para_lote_expirado(client, db_session):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto, lote = _criar_produto_e_lote(client, headers, dias_validade=-2)

    from uuid import UUID

    verificar_vencimentos_empresa(db_session, UUID(data["usuario"]["empresa_id"]))

    resp = client.get("/api/alertas", headers=headers)
    tipos = [a["tipo"] for a in resp.json()]
    assert "vencido" in tipos


def test_alerta_estoque_baixo(client, db_session):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    # estoque_minimo 5, quantidade 3 -> fica abaixo do minimo
    _criar_produto_e_lote(client, headers, dias_validade=60, estoque_minimo=5, quantidade=3)

    from uuid import UUID

    verificar_vencimentos_empresa(db_session, UUID(data["usuario"]["empresa_id"]))

    resp = client.get("/api/alertas", headers=headers)
    tipos = [a["tipo"] for a in resp.json()]
    assert "estoque_baixo" in tipos


def test_marcar_alerta_como_lido(client, db_session):
    from uuid import UUID

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    _criar_produto_e_lote(client, headers, dias_validade=-1)
    verificar_vencimentos_empresa(db_session, UUID(data["usuario"]["empresa_id"]))

    alerta = client.get("/api/alertas", headers=headers).json()[0]
    resp = client.put(f"/api/alertas/{alerta['id']}/ler", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["lido"] is True


def test_nao_duplica_alertas_ao_rodar_verificacao_duas_vezes(client, db_session):
    from uuid import UUID

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    _criar_produto_e_lote(client, headers, dias_validade=-1)
    empresa_id = UUID(data["usuario"]["empresa_id"])

    verificar_vencimentos_empresa(db_session, empresa_id)
    verificar_vencimentos_empresa(db_session, empresa_id)

    resp = client.get("/api/alertas", headers=headers)
    tipos_vencido = [a for a in resp.json() if a["tipo"] == "vencido"]
    assert len(tipos_vencido) == 1
