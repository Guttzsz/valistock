from app.config import Settings


def test_cors_aceita_dominio_novo_e_o_antigo_sem_repetir():
    s = Settings(frontend_url="https://valistock.vercel.app/", allowed_origins="https://valistock.com.br, https://www.valistock.com.br,https://valistock.vercel.app")
    assert s.cors_origins_list == ["https://valistock.vercel.app", "https://valistock.com.br", "https://www.valistock.com.br"]


def test_cors_padrao_inclui_o_dominio_proprio():
    s = Settings(frontend_url="https://valistock.vercel.app")
    assert "https://valistock.com.br" in s.cors_origins_list
    assert "https://valistock.vercel.app" in s.cors_origins_list


def test_cors_frontend_url_pode_ter_varios_enderecos():
    s = Settings(frontend_url="https://a.com,https://b.com", allowed_origins="")
    assert s.cors_origins_list == ["https://a.com", "https://b.com"]
