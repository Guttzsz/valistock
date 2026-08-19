from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProdutoCreate(BaseModel):
    codigo_barras: str | None = Field(default=None, max_length=50)
    nome: str = Field(min_length=2, max_length=150)
    descricao: str | None = None
    marca: str | None = None
    categoria_id: UUID | None = None
    fornecedor_id: UUID | None = None
    localizacao_id: UUID | None = None
    unidade_medida: str = "UN"
    preco_custo: Decimal = Field(ge=0, default=0)
    preco_venda: Decimal = Field(ge=0, default=0)
    estoque_minimo: int = Field(ge=0, default=0)


class ProdutoUpdate(BaseModel):
    codigo_barras: str | None = None
    nome: str | None = None
    descricao: str | None = None
    marca: str | None = None
    categoria_id: UUID | None = None
    fornecedor_id: UUID | None = None
    localizacao_id: UUID | None = None
    unidade_medida: str | None = None
    preco_custo: Decimal | None = Field(default=None, ge=0)
    preco_venda: Decimal | None = Field(default=None, ge=0)
    estoque_minimo: int | None = Field(default=None, ge=0)
    ativo: bool | None = None


class ProdutoOut(BaseModel):
    id: UUID
    codigo_barras: str | None
    nome: str
    descricao: str | None
    marca: str | None
    categoria_id: UUID | None
    categoria_nome: str | None = None
    fornecedor_id: UUID | None
    fornecedor_nome: str | None = None
    localizacao_id: UUID | None
    localizacao_nome: str | None = None
    unidade_medida: str
    preco_custo: Decimal
    preco_venda: Decimal
    estoque_atual: int
    estoque_minimo: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}
