from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from seed_demo_data import main as seed_demo_data


def ensure_sqlite_path(database_url: str) -> None:
    url = make_url(database_url)
    if url.drivername.startswith("sqlite") and url.database and url.database != ":memory:":
        database_path = Path(url.database)
        database_path.parent.mkdir(parents=True, exist_ok=True)
        if database_path.exists():
            database_path.unlink()


def main() -> None:
    settings = get_settings()
    ensure_sqlite_path(settings.database_url)
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    print(f"Bootstrapped local database at {settings.database_url}")


if __name__ == "__main__":
    main()
