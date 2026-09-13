from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.dependencies import get_session
from app.models.operacao import Cliente, Compra, CompraItem, Lote, MovimentacaoEstoque, Orcamento, OrcamentoItem, Usuario, Venda, VendaItem
from app.models.produto import Produto
from app.schemas.operacao import ClienteCreate, ClienteResponse, CompraCreate, CompraResponse, LoteCreate, LoteResponse, OrcamentoCreate, OrcamentoResponse, UsuarioCreate, UsuarioResponse, VendaCreate, VendaResponse
from app.services.security import hash_password

router = APIRouter(tags=["Operação"])

def one(session, model, item_id):
    item = session.get(model, item_id)
    if not item: raise HTTPException(404, "Recurso não encontrado.")
    return item

@router.post("/usuarios", response_model=UsuarioResponse, status_code=201)
def criar_usuario(payload: UsuarioCreate, session: Session = Depends(get_session)):
    if payload.perfil not in {"administrador", "gerente", "operador"}: raise HTTPException(422, "Perfil inválido.")
    item = Usuario(nome=payload.nome, email=payload.email.lower(), senha_hash=hash_password(payload.senha), perfil=payload.perfil); session.add(item)
    try: session.commit()
    except IntegrityError: session.rollback(); raise HTTPException(409, "E-mail já cadastrado.")
    session.refresh(item); return item

@router.get("/usuarios", response_model=list[UsuarioResponse])
def listar_usuarios(session: Session = Depends(get_session)): return session.scalars(select(Usuario).order_by(Usuario.nome)).all()

@router.post("/clientes", response_model=ClienteResponse, status_code=201)
def criar_cliente(payload: ClienteCreate, session: Session = Depends(get_session)):
    item = Cliente(**payload.model_dump()); session.add(item)
    try: session.commit()
    except IntegrityError: session.rollback(); raise HTTPException(409, "CPF/CNPJ já cadastrado.")
    session.refresh(item); return item

@router.get("/clientes", response_model=list[ClienteResponse])
def listar_clientes(session: Session = Depends(get_session)): return session.scalars(select(Cliente).order_by(Cliente.nome)).all()

@router.get("/clientes/{cliente_id}", response_model=ClienteResponse)
def buscar_cliente(cliente_id: int, session: Session = Depends(get_session)): return one(session, Cliente, cliente_id)

@router.post("/lotes", response_model=LoteResponse, status_code=201)
def criar_lote(payload: LoteCreate, session: Session = Depends(get_session)):
    one(session, Produto, payload.produto_id)
    if payload.validade < date.today(): raise HTTPException(422, "A validade não pode estar no passado.")
    item = Lote(**payload.model_dump()); session.add(item); session.flush()
    session.add(MovimentacaoEstoque(lote_id=item.id, tipo="entrada", quantidade=item.quantidade, origem="cadastro", observacao="Saldo inicial do lote"))
    session.commit(); session.refresh(item); return item

@router.get("/lotes", response_model=list[LoteResponse])
def listar_lotes(produto_id: int | None = None, session: Session = Depends(get_session)):
    query = select(Lote).order_by(Lote.validade)
    if produto_id: query = query.where(Lote.produto_id == produto_id)
    return session.scalars(query).all()

@router.post("/compras", response_model=CompraResponse, status_code=201)
def registrar_compra(payload: CompraCreate, session: Session = Depends(get_session)):
    compra = Compra(numero=payload.numero, observacao=payload.observacao); session.add(compra); session.flush(); total = Decimal("0")
    try:
        for data in payload.itens:
            lote = one(session, Lote, data.lote_id); lote.quantidade += data.quantidade
            session.add(CompraItem(compra_id=compra.id, lote_id=lote.id, quantidade=data.quantidade, custo_unitario=data.custo_unitario))
            session.add(MovimentacaoEstoque(lote_id=lote.id, tipo="entrada", quantidade=data.quantidade, origem="compra", observacao=f"Compra {payload.numero}")); total += data.quantidade * data.custo_unitario
        compra.total = total; session.commit()
    except IntegrityError: session.rollback(); raise HTTPException(409, "Número de compra já cadastrado.")
    session.refresh(compra); return compra

@router.post("/orcamentos", response_model=OrcamentoResponse, status_code=201)
def criar_orcamento(payload: OrcamentoCreate, session: Session = Depends(get_session)):
    if payload.cliente_id: one(session, Cliente, payload.cliente_id)
    item = Orcamento(cliente_id=payload.cliente_id); session.add(item); session.flush(); total = Decimal("0")
    for data in payload.itens:
        produto = one(session, Produto, data.produto_id); session.add(OrcamentoItem(orcamento_id=item.id, produto_id=produto.id, quantidade=data.quantidade, preco_unitario=data.preco_unitario)); total += data.quantidade * data.preco_unitario
    item.total = total; session.commit(); session.refresh(item); return item

@router.get("/orcamentos", response_model=list[OrcamentoResponse])
def listar_orcamentos(session: Session = Depends(get_session)): return session.scalars(select(Orcamento).order_by(Orcamento.criado_em.desc())).all()

@router.post("/vendas", response_model=VendaResponse, status_code=201)
def finalizar_venda(payload: VendaCreate, usuario_id: int, session: Session = Depends(get_session)):
    usuario = one(session, Usuario, usuario_id)
    if not usuario.ativo: raise HTTPException(403, "Usuário inativo.")
    if payload.cliente_id: one(session, Cliente, payload.cliente_id)
    venda = Venda(cliente_id=payload.cliente_id, usuario_id=usuario_id, forma_pagamento=payload.forma_pagamento); session.add(venda); session.flush(); total = Decimal("0")
    for data in payload.itens:
        produto = one(session, Produto, data.produto_id)
        if not produto.ativo: raise HTTPException(422, f"Produto {produto.nome} está inativo.")
        restantes = data.quantidade
        lotes = session.scalars(select(Lote).where(Lote.produto_id == produto.id, Lote.quantidade > 0, Lote.validade >= date.today()).order_by(Lote.validade)).all()
        if sum((l.quantidade for l in lotes), Decimal("0")) < restantes: raise HTTPException(422, f"Estoque insuficiente para {produto.nome}.")
        for lote in lotes:
            retirada = min(restantes, lote.quantidade)
            if retirada:
                lote.quantidade -= retirada; restantes -= retirada
                session.add(VendaItem(venda_id=venda.id, lote_id=lote.id, produto_id=produto.id, quantidade=retirada, preco_unitario=produto.preco_venda))
                session.add(MovimentacaoEstoque(lote_id=lote.id, tipo="saida", quantidade=retirada, origem="venda", observacao=f"Venda {venda.id}")); total += retirada * produto.preco_venda
            if restantes == 0: break
    venda.total = total; session.commit(); session.refresh(venda); return venda

@router.get("/vendas", response_model=list[VendaResponse])
def listar_vendas(session: Session = Depends(get_session)): return session.scalars(select(Venda).order_by(Venda.criado_em.desc())).all()

@router.get("/relatorios/resumo")
def resumo(session: Session = Depends(get_session)):
    hoje = date.today()
    valor_vendas = session.scalar(select(func.coalesce(func.sum(Venda.total), 0)))
    estoque_baixo = session.scalar(select(func.count()).select_from(Produto).where(Produto.ativo == True, Produto.estoque_minimo > func.coalesce(select(func.sum(Lote.quantidade)).where(Lote.produto_id == Produto.id).scalar_subquery(), 0)))
    vencendo = session.scalar(select(func.count()).select_from(Lote).where(Lote.validade <= hoje.fromordinal(hoje.toordinal() + 30), Lote.quantidade > 0))
    return {"total_vendas": valor_vendas, "produtos_estoque_baixo": estoque_baixo, "lotes_vencendo_em_30_dias": vencendo}
