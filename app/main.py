from fastapi import FastAPI

from app.api.health import router as health_router


app = FastAPI(
    title="SellFlow API",
    description="API de gestão de vendas do SellFlow.",
    version="0.1.0",
)

app.include_router(health_router)
