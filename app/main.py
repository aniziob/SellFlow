from fastapi import FastAPI
from app.core.config import settings
from app.database.base import Base
from app.database.connection import engine
import app.models

from app.api.health import router as health_router
from app.api.catalogo import router as catalogo_router
from app.api.operacao import router as operacao_router


app = FastAPI(
    title="SellFlow API",
    description="API de gestão de vendas do SellFlow.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(catalogo_router)
app.include_router(operacao_router)


@app.on_event("startup")
def initialize_standalone_database() -> None:
    if settings.standalone_mode:
        Base.metadata.create_all(bind=engine)
