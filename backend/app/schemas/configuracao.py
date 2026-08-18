from pydantic import BaseModel, Field


class ConfiguracaoUpdate(BaseModel):
    dias_alerta_1: int = Field(gt=0)
    dias_alerta_2: int = Field(gt=0)
    dias_alerta_3: int = Field(gt=0)


class ConfiguracaoOut(BaseModel):
    dias_alerta_1: int
    dias_alerta_2: int
    dias_alerta_3: int

    model_config = {"from_attributes": True}
