"""cria entidades operacionais do SellFlow

Revision ID: 8a1c2d3e4f5a
Revises: 49794418a1d1
"""
from alembic import op
import sqlalchemy as sa

revision = "8a1c2d3e4f5a"
down_revision = "49794418a1d1"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("usuarios", sa.Column("id", sa.Integer, primary_key=True), sa.Column("nome", sa.String(150), nullable=False), sa.Column("email", sa.String(150), nullable=False, unique=True), sa.Column("senha_hash", sa.String(255), nullable=False), sa.Column("perfil", sa.String(30), nullable=False), sa.Column("ativo", sa.Boolean, nullable=False), sa.Column("criado_em", sa.DateTime, nullable=False))
    op.create_table("clientes", sa.Column("id", sa.Integer, primary_key=True), sa.Column("nome", sa.String(200), nullable=False), sa.Column("cpf_cnpj", sa.String(20), unique=True), sa.Column("telefone", sa.String(30)), sa.Column("email", sa.String(150)), sa.Column("endereco", sa.Text), sa.Column("criado_em", sa.DateTime, nullable=False))
    op.create_table("lotes", sa.Column("id", sa.Integer, primary_key=True), sa.Column("produto_id", sa.Integer, sa.ForeignKey("produtos.id"), nullable=False), sa.Column("codigo", sa.String(80), nullable=False), sa.Column("validade", sa.Date, nullable=False), sa.Column("localizacao", sa.String(120)), sa.Column("quantidade", sa.Numeric(12,3), nullable=False), sa.Column("custo_unitario", sa.Numeric(10,2), nullable=False), sa.Column("criado_em", sa.DateTime, nullable=False))
    op.create_index("ix_lotes_produto_id", "lotes", ["produto_id"])
    op.create_table("movimentacoes_estoque", sa.Column("id", sa.Integer, primary_key=True), sa.Column("lote_id", sa.Integer, sa.ForeignKey("lotes.id"), nullable=False), sa.Column("tipo", sa.String(20), nullable=False), sa.Column("quantidade", sa.Numeric(12,3), nullable=False), sa.Column("origem", sa.String(30), nullable=False), sa.Column("observacao", sa.Text), sa.Column("criado_em", sa.DateTime, nullable=False))
    op.create_index("ix_movimentacoes_estoque_lote_id", "movimentacoes_estoque", ["lote_id"])
    op.create_table("compras", sa.Column("id", sa.Integer, primary_key=True), sa.Column("numero", sa.String(50), nullable=False, unique=True), sa.Column("data_compra", sa.DateTime, nullable=False), sa.Column("total", sa.Numeric(12,2), nullable=False), sa.Column("observacao", sa.Text))
    op.create_table("compra_itens", sa.Column("id", sa.Integer, primary_key=True), sa.Column("compra_id", sa.Integer, sa.ForeignKey("compras.id"), nullable=False), sa.Column("lote_id", sa.Integer, sa.ForeignKey("lotes.id"), nullable=False), sa.Column("quantidade", sa.Numeric(12,3), nullable=False), sa.Column("custo_unitario", sa.Numeric(10,2), nullable=False))
    op.create_table("orcamentos", sa.Column("id", sa.Integer, primary_key=True), sa.Column("cliente_id", sa.Integer, sa.ForeignKey("clientes.id")), sa.Column("status", sa.String(20), nullable=False), sa.Column("total", sa.Numeric(12,2), nullable=False), sa.Column("criado_em", sa.DateTime, nullable=False))
    op.create_table("orcamento_itens", sa.Column("id", sa.Integer, primary_key=True), sa.Column("orcamento_id", sa.Integer, sa.ForeignKey("orcamentos.id"), nullable=False), sa.Column("produto_id", sa.Integer, sa.ForeignKey("produtos.id"), nullable=False), sa.Column("quantidade", sa.Numeric(12,3), nullable=False), sa.Column("preco_unitario", sa.Numeric(10,2), nullable=False))
    op.create_table("vendas", sa.Column("id", sa.Integer, primary_key=True), sa.Column("cliente_id", sa.Integer, sa.ForeignKey("clientes.id")), sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id"), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("forma_pagamento", sa.String(30), nullable=False), sa.Column("total", sa.Numeric(12,2), nullable=False), sa.Column("criado_em", sa.DateTime, nullable=False))
    op.create_table("venda_itens", sa.Column("id", sa.Integer, primary_key=True), sa.Column("venda_id", sa.Integer, sa.ForeignKey("vendas.id"), nullable=False), sa.Column("lote_id", sa.Integer, sa.ForeignKey("lotes.id"), nullable=False), sa.Column("produto_id", sa.Integer, sa.ForeignKey("produtos.id"), nullable=False), sa.Column("quantidade", sa.Numeric(12,3), nullable=False), sa.Column("preco_unitario", sa.Numeric(10,2), nullable=False))

def downgrade():
    op.drop_table("venda_itens"); op.drop_table("vendas"); op.drop_table("orcamento_itens"); op.drop_table("orcamentos"); op.drop_table("compra_itens"); op.drop_table("compras"); op.drop_index("ix_movimentacoes_estoque_lote_id", table_name="movimentacoes_estoque"); op.drop_table("movimentacoes_estoque"); op.drop_index("ix_lotes_produto_id", table_name="lotes"); op.drop_table("lotes"); op.drop_table("clientes"); op.drop_table("usuarios")
