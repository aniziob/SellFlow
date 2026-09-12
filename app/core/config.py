from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_server: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str

    rabbitmq_host: str
    rabbitmq_port: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
