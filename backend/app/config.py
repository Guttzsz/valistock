from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Prefixos que provedores (Supabase, Render, Heroku) entregam na connection string; o driver instalado e o psycopg2.
_PREFIXOS_POSTGRES = ("postgres://", "postgresql://", "postgresql+psycopg://")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    secret_key: str = "insecure-dev-key-change-me"
    access_token_expire_minutes: int = 1440
    mfa_encryption_key: str = ""
    timezone: str = "America/Sao_Paulo"

    database_url: str = "postgresql+psycopg2://valistock:valistock@localhost:5432/valistock"

    # Hosts aceitos pelo TrustedHostMiddleware em producao, separados por virgula.
    allowed_hosts: str = "valistock-backend.onrender.com"

    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""

    frontend_url: str = "http://localhost:5500"
    backend_url: str = "http://localhost:8000"

    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_essencial: str = ""
    stripe_price_profissional: str = ""
    stripe_price_empresa: str = ""
    stripe_success_url: str = "http://localhost:5500/templates/planos.html?status=success"
    stripe_cancel_url: str = "http://localhost:5500/templates/planos.html?status=cancel"

    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_admin_email: str = ""

    @field_validator("database_url")
    @classmethod
    def usar_driver_psycopg2(cls, valor: str) -> str:
        for prefixo in _PREFIXOS_POSTGRES:
            if valor.startswith(prefixo):
                return "postgresql+psycopg2://" + valor[len(prefixo):]
        return valor

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
