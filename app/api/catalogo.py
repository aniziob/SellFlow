from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.dependencies import get_session
from app.models.categoria import Categoria
from app.models.produto import Produto
from app.schemas.categoria import CategoriaCreate, CategoriaResponse
from app.schemas.operacao import ProdutoCreate, ProdutoResponse

router = APIRouter(tags=["Catálogo"])

def get_or_404(session, model, item_id):
    item = session.get(model, item_id)
    if not item: raise HTTPException(404, "Recurso não encontrado.")
    return item

@router.post("/categorias", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def criar_categoria(payload: CategoriaCreate, session: Session = Depends(get_session)):
    item = Categoria(**payload.model_dump()); session.add(item)
    try: session.commit()
    except IntegrityError: session.rollback(); raise HTTPException(409, "Já existe uma categoria com este nome.")
    session.refresh(item); return item

@router.get("/categorias", response_model=list[CategoriaResponse])
def listar_categorias(session: Session = Depends(get_session)): return session.scalars(select(Categoria).order_by(Categoria.nome)).all()

@router.get("/categorias/{categoria_id}", response_model=CategoriaResponse)
def buscar_categoria(categoria_id: int, session: Session = Depends(get_session)): return get_or_404(session, Categoria, categoria_id)

@router.post("/produtos", response_model=ProdutoResponse, status_code=201)
def criar_produto(payload: ProdutoCreate, session: Session = Depends(get_session)):
    get_or_404(session, Categoria, payload.categoria_id); item = Produto(**payload.model_dump()); session.add(item)
    try: session.commit()
    except IntegrityError: session.rollback(); raise HTTPException(409, "Código de barras já cadastrado.")
    session.refresh(item); return item

@router.get("/produtos", response_model=list[ProdutoResponse])
def listar_produtos(ativos: bool | None = None, session: Session = Depends(get_session)):
    query = select(Produto).order_by(Produto.nome)
    if ativos is not None: query = query.where(Produto.ativo == ativos)
    return session.scalars(query).all()

@router.get("/produtos/{produto_id}", response_model=ProdutoResponse)
def buscar_produto(produto_id: int, session: Session = Depends(get_session)): return get_or_404(session, Produto, produto_id)

@router.put("/produtos/{produto_id}", response_model=ProdutoResponse)
def atualizar_produto(produto_id: int, payload: ProdutoCreate, session: Session = Depends(get_session)):
    get_or_404(session, Categoria, payload.categoria_id); item = get_or_404(session, Produto, produto_id)
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    try: session.commit()
    except IntegrityError: session.rollback(); raise HTTPException(409, "Código de barras já cadastrado.")
    session.refresh(item); return item

@router.delete("/produtos/{produto_id}", status_code=204)
def desativar_produto(produto_id: int, session: Session = Depends(get_session)):
    item = get_or_404(session, Produto, produto_id); item.ativo = False; session.commit()
