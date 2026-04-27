import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

load_dotenv()


def get_db_dialect() -> str:
    raw = os.getenv("DB_DIALECT", "postgresql").strip().lower()
    if raw not in {"postgresql", "mysql"}:
        raise ValueError("DB_DIALECT must be 'postgresql' or 'mysql'")
    return raw


def get_database_url() -> str:
    dialect = get_db_dialect()
    host = os.getenv("DB_HOST", "localhost")
    default_port = "5432" if dialect == "postgresql" else "3306"
    port = os.getenv("DB_PORT", default_port)
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD", "")

    if not database or not user:
        raise ValueError(
            "Set DB_DIALECT/DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD in .env"
        )

    if dialect == "postgresql":
        return f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{database}"
    return f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{database}"


DATABASE_URL = get_database_url()
engine: Engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
