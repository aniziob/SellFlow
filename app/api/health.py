from fastapi import APIRouter
from sqlalchemy import text

from app.database.connection import engine
from app.messaging.rabbitmq import create_rabbitmq_connection


router = APIRouter()


@router.get("/health")
def health_check():
    database_status = "disconnected"
    rabbitmq_status = "disconnected"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            database_status = "connected"
    except Exception:
        database_status = "disconnected"

    try:
        connection = create_rabbitmq_connection()
        connection.close()
        rabbitmq_status = "connected"
    except Exception:
        rabbitmq_status = "disconnected"

    return {
        "status": "ok",
        "service": "sellflow-api",
        "database": database_status,
        "rabbitmq": rabbitmq_status,
    }
