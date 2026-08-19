from pydantic import BaseModel


class PreferenciaNotificacaoIn(BaseModel):
    produtos_vencendo: bool = True
    produtos_vencidos: bool = True
    estoque_baixo: bool = True
    novas_perdas: bool = False
    relatorios: bool = False
    avisos_administrativos: bool = True


class PreferenciaNotificacaoOut(PreferenciaNotificacaoIn):
    model_config = {"from_attributes": True}


class PreferenciaDashboardIn(BaseModel):
    widgets_ativos: list[str]


class PreferenciaDashboardOut(BaseModel):
    widgets_ativos: list[str]
