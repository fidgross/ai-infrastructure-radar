from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.explorer import router as explorer_router
from app.api.routes.health import router as health_router
from app.api.routes.operations import router as operations_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.project_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.backend_trusted_hosts)

app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(explorer_router)
app.include_router(operations_router)
