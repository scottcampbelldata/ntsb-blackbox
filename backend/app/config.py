import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Black Box AI"
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'data' / 'ntsb.db'}")
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
        if origin.strip()
    )
    query_timeout_ms: int = int(os.getenv("QUERY_TIMEOUT_MS", "5000"))
    max_rows: int = int(os.getenv("MAX_QUERY_ROWS", "500"))
    retrieval_pool: int = int(os.getenv("RETRIEVAL_POOL", "80"))
    retrieval_k: int = int(os.getenv("RETRIEVAL_K", "5"))

    @property
    def is_postgres(self):
        return self.database_url.startswith(("postgresql://", "postgres://"))

    @property
    def is_sqlite(self):
        return self.database_url.startswith("sqlite:///")


settings = Settings()
