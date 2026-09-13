from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


if settings.standalone_mode:
    data_dir = Path(settings.standalone_data_dir or Path.cwd() / "data")
    data_dir.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite:///{data_dir / 'sellflow.db'}"
else:
    database_url = URL.create(
        drivername="mssql+pyodbc",
        username=settings.database_user,
        password=settings.database_password,
        host=settings.database_server,
        port=settings.database_port,
        database=settings.database_name,
        query={"driver": "ODBC Driver 18 for SQL Server", "TrustServerCertificate": "yes"},
    )

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.standalone_mode else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
