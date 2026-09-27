from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

settings = get_settings()

# Instancia unica compartilhada entre main.py (middleware/handler) e as rotas que
# precisam de throttling (login, verificacao de MFA). Em memoria: suficiente para uma
# unica instancia do servico no Render; se um dia escalar para varias instancias,
# passar a usar um storage_uri com Redis (parametro do Limiter).
# Desligado em teste (APP_ENV=test, ver tests/conftest.py): a suite roda dezenas de
# logins/registros no mesmo IP em menos de um minuto, o que estouraria o limite e
# quebraria testes sem relacao nenhuma com o throttling em si.
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.app_env != "test",
    default_limits=["200/minute"],  # teto geral pra qualquer rota que nao tenha um limite proprio
)
