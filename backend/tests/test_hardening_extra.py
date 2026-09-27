from app.main import MAX_BODY_BYTES


def test_corpo_muito_grande_e_recusado(client):
    resp = client.post(
        "/api/auth/login",
        content=b"a" * (MAX_BODY_BYTES + 1),
        headers={"Content-Type": "application/json", "Content-Length": str(MAX_BODY_BYTES + 1)},
    )
    assert resp.status_code == 413


def test_corpo_normal_passa(client):
    resp = client.post("/api/auth/login", json={"email": "ninguem@example.com", "senha": "x"})
    assert resp.status_code != 413
