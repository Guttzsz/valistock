from tests.conftest import auth_headers, registrar_empresa


def test_register_cria_empresa_e_admin(client):
    data = registrar_empresa(client, "a")
    assert data["usuario"]["perfil"] == "administrador"
    assert "access_token" in data


def test_register_com_email_duplicado_falha(client):
    registrar_empresa(client, "a")
    resp = client.post(
        "/api/auth/register",
        json={
            "empresa_nome_fantasia": "Outro Mercado",
            "empresa_email": "outro@example.com",
            "admin_nome": "Outro Admin",
            "admin_email": "admina@example.com",
            "admin_senha": "SenhaForte123!",
        },
    )
    assert resp.status_code == 409


def test_login_com_credenciais_corretas(client):
    registrar_empresa(client, "a")
    resp = client.post("/api/auth/login", json={"email": "admina@example.com", "senha": "SenhaForte123!"})
    assert resp.status_code == 200
    assert resp.json()["usuario"]["email"] == "admina@example.com"


def test_login_com_senha_incorreta_falha(client):
    registrar_empresa(client, "a")
    resp = client.post("/api/auth/login", json={"email": "admina@example.com", "senha": "senha-errada"})
    assert resp.status_code == 401


def test_login_com_email_inexistente_falha(client):
    resp = client.post("/api/auth/login", json={"email": "naoexiste@example.com", "senha": "qualquer"})
    assert resp.status_code == 401


def test_rota_protegida_sem_token_falha(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 401


def test_rota_protegida_com_token_funciona(client):
    data = registrar_empresa(client, "a")
    resp = client.get("/api/auth/me", headers=auth_headers(data["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["email"] == "admina@example.com"


def test_senha_e_armazenada_com_hash(client, db_session):
    registrar_empresa(client, "a")
    from app.models.usuario import Usuario

    usuario = db_session.query(Usuario).filter(Usuario.email == "admina@example.com").first()
    assert usuario.senha_hash != "SenhaForte123!"
    assert usuario.senha_hash.startswith("$2b$")
