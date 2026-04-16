from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.seeds import seed_if_enabled


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        seed_if_enabled()
        yield

    app = FastAPI(title="MHC Cloud Panel", version="0.1.0", lifespan=lifespan)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.parsed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_, exc: AppError):
        return exc_to_response(exc)

    return app


def exc_to_response(exc: AppError):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details or {}}},
    )


app = create_app()
