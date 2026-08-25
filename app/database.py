from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(
    settings.database_url,
    echo=settings.app_env == "development" and not settings.is_production,
    connect_args=connect_args,
)


def run_migrations() -> None:
    """Adiciona colunas novas a bases de dados SQLite existentes."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    with engine.begin() as conn:
        if "telegram_chat_id" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN telegram_chat_id VARCHAR"))
        if "telegram_user_id" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN telegram_user_id VARCHAR"))


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    run_migrations()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
