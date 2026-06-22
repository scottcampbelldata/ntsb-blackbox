from fastapi import APIRouter

from backend.app.config import settings
from backend.app.data.status import get_data_status


router = APIRouter()


@router.get("/health")
def health():
    return {
        "ok": True,
        "app": settings.app_name,
        "database": "postgres" if settings.is_postgres else "sqlite" if settings.is_sqlite else "unknown",
        "data": get_data_status(),
    }
