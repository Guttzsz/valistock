from app.rate_limit import limiter


def test_login_e_bloqueado_apos_muitas_tentativas(client):
    """O limiter fica desligado durante os testes (ver conftest.py) para nao quebrar a
    suite inteira com 429s. Este teste liga ele de proposito, so aqui, pra provar que o
    throttling realmente funciona (nao so que o decorator esta presente no codigo)."""
    limiter.enabled = True
    limiter.reset()
    try:
        respostas = [
            client.post("/api/auth/login", json={"email": "ninguem@example.com", "senha": "errada"}) for _ in range(15)
        ]
    finally:
        limiter.enabled = False
        limiter.reset()

    codigos = [r.status_code for r in respostas]
    assert 429 in codigos, f"esperava pelo menos um 429 entre 15 tentativas rapidas, recebi: {codigos}"
    assert codigos[:10].count(429) == 0, "as primeiras 10 tentativas (dentro do limite) nao deveriam ser bloqueadas"


def test_respostas_incluem_headers_de_seguranca(client):
    resp = client.get("/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "strict-origin-when-cross-origin"
