from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProdutoBase(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    codigo_barras: str | None = None
    categoria_id: int
    principio_ativo: str | None = None
    concentracao: str | None = None
    forma_farmaceutica: str | None = None
    apresentacao: str | None = None
    fabricante: str | None = None
    registro_anvisa: str | None = None
    descricao: str | None = None
    preco_custo: Decimal = Field(ge=0)
    preco_venda: Decimal = Field(ge=0)
    estoque_minimo: Decimal = Field(default=0, ge=0)
    ativo: bool = True
class ProdutoCreate(ProdutoBase): pass
class ProdutoResponse(ProdutoBase, ORM): id: int

class ClienteBase(BaseModel):
    nome: str = Field(min_length=1)
    cpf_cnpj: str | None = None
    telefone: str | None = None
    email: str | None = None
    endereco: str | None = None
class ClienteCreate(ClienteBase): pass
class ClienteResponse(ClienteBase, ORM): id: int; criado_em: datetime

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str = Field(min_length=8)
    perfil: str = "operador"
class UsuarioResponse(ORM):
    id: int; nome: str; email: str; perfil: str; ativo: bool; criado_em: datetime

class LoteCreate(BaseModel):
    produto_id: int; codigo: str; validade: date; localizacao: str | None = None
    quantidade: Decimal = Field(gt=0); custo_unitario: Decimal = Field(ge=0)
class LoteResponse(LoteCreate, ORM): id: int; criado_em: datetime

class CompraItemCreate(BaseModel): lote_id: int; quantidade: Decimal = Field(gt=0); custo_unitario: Decimal = Field(ge=0)
class CompraCreate(BaseModel): numero: str; itens: list[CompraItemCreate] = Field(min_length=1); observacao: str | None = None
class CompraResponse(ORM): id: int; numero: str; total: Decimal; data_compra: datetime; observacao: str | None

class VendaItemCreate(BaseModel): produto_id: int; quantidade: Decimal = Field(gt=0)
class VendaCreate(BaseModel): cliente_id: int | None = None; forma_pagamento: str; itens: list[VendaItemCreate] = Field(min_length=1)
class VendaResponse(ORM): id: int; cliente_id: int | None; usuario_id: int; status: str; forma_pagamento: str; total: Decimal; criado_em: datetime

class OrcamentoItemCreate(BaseModel): produto_id: int; quantidade: Decimal = Field(gt=0); preco_unitario: Decimal = Field(ge=0)
class OrcamentoCreate(BaseModel): cliente_id: int | None = None; itens: list[OrcamentoItemCreate] = Field(min_length=1)
class OrcamentoResponse(ORM): id: int; cliente_id: int | None; status: str; total: Decimal; criado_em: datetime
