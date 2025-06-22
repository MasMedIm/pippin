import os

from sqlalchemy import create_engine, text


def get_database_url() -> str:
    """Compose the database URL from environment variables."""
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "pippindb")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


# Create a global engine. For a real-world project we would use sessionmakers,
# connection pools, and possibly async SQLAlchemy, but for a quick skeleton this
# suffices.
engine = create_engine(get_database_url(), pool_pre_ping=True)


def health_check() -> bool:
    """Run a simple query (SELECT 1) against the database to check connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # pragma: no cover – basic skeleton
        print("Database health check failed:", exc)
        return False
