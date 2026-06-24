from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.analyses import router as analyses_router
from backend.app.api.ask import router as ask_router
from backend.app.api.context import router as context_router
from backend.app.api.dataset import router as dataset_router
from backend.app.api.health import router as health_router
from backend.app.config import settings


def create_app():
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(ask_router)
    app.include_router(analyses_router)
    app.include_router(dataset_router)
    app.include_router(context_router)
    return app


app = create_app()
