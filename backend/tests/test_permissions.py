from tests.conftest import auth_headers, registrar_empresa


def _criar_funcionario(client, headers):
    resp = client.post(
        "/api/usuarios",
        json={"nome": "Funcionario", "email": "func@example.com", "senha": "SenhaForte123!", "perfil": "funcionario"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


def test_admin_pode_criar_usuario(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    _criar_funcionario(client, headers)


def test_funcionario_nao_pode_criar_usuario(client):
    data = registrar_empresa(client, "a")
    headers_admin = auth_headers(data["access_token"])
    _criar_funcionario(client, headers_admin)

    login = client.post("/api/auth/login", json={"email": "func@example.com", "senha": "SenhaForte123!"}).json()
    headers_func = auth_headers(login["access_token"])

    resp = client.post(
        "/api/usuarios",
        json={"nome": "Outro", "email": "outro@example.com", "senha": "SenhaForte123!", "perfil": "funcionario"},
        headers=headers_func,
    )
    assert resp.status_code == 403


def test_funcionario_pode_criar_produto(client):
    data = registrar_empresa(client, "a")
    headers_admin = auth_headers(data["access_token"])
    _criar_funcionario(client, headers_admin)

    login = client.post("/api/auth/login", json={"email": "func@example.com", "senha": "SenhaForte123!"}).json()
    headers_func = auth_headers(login["access_token"])

    resp = client.post(
        "/api/produtos", json={"nome": "Produto Func", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers_func
    )
    assert resp.status_code == 201


def test_funcionario_nao_pode_alterar_configuracoes(client):
    data = registrar_empresa(client, "a")
    headers_admin = auth_headers(data["access_token"])
    _criar_funcionario(client, headers_admin)

    login = client.post("/api/auth/login", json={"email": "func@example.com", "senha": "SenhaForte123!"}).json()
    headers_func = auth_headers(login["access_token"])

    resp = client.put("/api/configuracoes/alertas", json={"dias_alerta_1": 10, "dias_alerta_2": 5, "dias_alerta_3": 2}, headers=headers_func)
    assert resp.status_code == 403
