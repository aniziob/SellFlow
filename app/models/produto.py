from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    nome: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    codigo_barras: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
    )

    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id"),
        nullable=False,
    )

    principio_ativo: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    concentracao: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    forma_farmaceutica: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    apresentacao: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    fabricante: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    registro_anvisa: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preco_custo: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    preco_venda: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    estoque_minimo: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
        default=0,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    categoria = relationship(
        "Categoria",
        backref="produtos",
    )
