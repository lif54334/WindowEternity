from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import DATA_DIR, DATABASE_URL

Base = declarative_base()
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    from app import models  # noqa: F401 - registers models with SQLAlchemy metadata

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_sqlite_columns() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    column_specs = {
        "settings": {
            "refresh_time_of_day": "VARCHAR(5) NOT NULL DEFAULT '09:00'",
            "font_size_percent": "INTEGER NOT NULL DEFAULT 100",
            "llm_custom_prompt": "TEXT",
        },
        "repositories": {
            "detail_description": "TEXT",
            "topics": "TEXT",
            "readme_excerpt": "TEXT",
        },
        "refresh_runs": {
            "ai_summary_status": "VARCHAR(32)",
            "ai_summary": "TEXT",
            "ai_summary_error": "TEXT",
        },
    }
    with engine.begin() as connection:
        for table_name, columns in column_specs.items():
            if table_name not in table_names:
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_type in columns.items():
                if column_name not in existing:
                    connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")