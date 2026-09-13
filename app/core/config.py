from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    database_server: str | None = None
    database_port: int = 1433
    database_name: str | None = None
    database_user: str | None = None
    database_password: str | None = None
    standalone_mode: bool = False
    standalone_data_dir: str | None = None

    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
