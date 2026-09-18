"""Database initialization helpers."""

from pathlib import Path

from sqlalchemy.orm import sessionmaker

from backend.app.database.models import Base, create_database_engine


def ensure_sqlite_directory(database_url: str) -> None:
    """Create the local SQLite directory when the configured URL uses a file."""
    prefix = "sqlite:///"
    if database_url.startswith(prefix) and not database_url.startswith("sqlite:///:memory:"):
        database_path = Path(database_url[len(prefix):])
        database_path.parent.mkdir(parents=True, exist_ok=True)


def initialize_database(database_url: str):
    """Create tables and return a SQLAlchemy session factory."""
    ensure_sqlite_directory(database_url)
    engine = create_database_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
