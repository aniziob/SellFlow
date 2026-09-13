from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(30), nullable=False, default="operador")
    ativo: Mapped[bool] = mapped_column(default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Cliente(Base):
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cpf_cnpj: Mapped[str | None] = mapped_column(String(20), unique=True)
    telefone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(150))
    endereco: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Lote(Base):
    __tablename__ = "lotes"
    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(80), nullable=False)
    validade: Mapped[date] = mapped_column(Date, nullable=False)
    localizacao: Mapped[str | None] = mapped_column(String(120))
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    custo_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"
    id: Mapped[int] = mapped_column(primary_key=True)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lotes.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    origem: Mapped[str] = mapped_column(String(30), nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Compra(Base):
    __tablename__ = "compras"
    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    data_compra: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    observacao: Mapped[str | None] = mapped_column(Text)


class CompraItem(Base):
    __tablename__ = "compra_itens"
    id: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras.id"), nullable=False)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lotes.id"), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


class Orcamento(Base):
    __tablename__ = "orcamentos"
    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="aberto")
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class OrcamentoItem(Base):
    __tablename__ = "orcamento_itens"
    id: Mapped[int] = mapped_column(primary_key=True)
    orcamento_id: Mapped[int] = mapped_column(ForeignKey("orcamentos.id"), nullable=False)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


class Venda(Base):
    __tablename__ = "vendas"
    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="concluida")
    forma_pagamento: Mapped[str] = mapped_column(String(30), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class VendaItem(Base):
    __tablename__ = "venda_itens"
    id: Mapped[int] = mapped_column(primary_key=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas.id"), nullable=False)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lotes.id"), nullable=False)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
