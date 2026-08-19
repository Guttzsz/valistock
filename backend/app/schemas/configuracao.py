from pydantic import BaseModel, Field

TIPOS_ESTABELECIMENTO = ["mercado", "hortifruti", "padaria", "quitanda", "acougue", "conveniencia", "outro"]


class ConfiguracaoAlertasUpdate(BaseModel):
    dias_alerta_1: int = Field(gt=0)
    dias_alerta_2: int = Field(gt=0)
    dias_alerta_3: int = Field(gt=0)


class ConfiguracaoEmpresaUpdate(BaseModel):
    tipo_estabelecimento: str | None = None
    fuso_horario: str | None = None
    moeda: str | None = None
    formato_data: str | None = None
    cor_principal: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    logo_url: str | None = None
    horario_funcionamento: str | None = None


class OnboardingEtapaUpdate(BaseModel):
    etapa: int = Field(ge=1, le=9)
    tipo_estabelecimento: str | None = None
    tipo_estabelecimento_outro: str | None = None
    quantidade_funcionarios_aprox: str | None = None
    quantidade_produtos_aprox: str | None = None
    categorias_iniciais: list[str] | None = None
    dias_alerta_1: int | None = None
    dias_alerta_2: int | None = None
    dias_alerta_3: int | None = None
    concluir: bool = False


class ConfiguracaoOut(BaseModel):
    dias_alerta_1: int
    dias_alerta_2: int
    dias_alerta_3: int
    tipo_estabelecimento: str | None
    fuso_horario: str
    moeda: str
    formato_data: str
    cor_principal: str
    logo_url: str | None
    horario_funcionamento: str | None
    onboarding_concluido: bool
    onboarding_etapa: int
    quantidade_funcionarios_aprox: str | None
    quantidade_produtos_aprox: str | None

    model_config = {"from_attributes": True}
