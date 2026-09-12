import pika

from app.core.config import settings


def create_rabbitmq_connection():
    parameters = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
    )

    return pika.BlockingConnection(parameters)
