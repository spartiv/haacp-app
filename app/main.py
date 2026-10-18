from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.error_handlers import (
    app_error_handler,
    domain_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.errors import AppError, DomainError
from app.core.frontend import mount_frontend
from app.core.logging_config import configure_logging
from app.routers.v1 import api_router


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Polton HACCP API")
    app.include_router(api_router)
    app.exception_handler(AppError)(app_error_handler)
    app.exception_handler(DomainError)(domain_error_handler)
    app.exception_handler(StarletteHTTPException)(http_exception_handler)
    app.exception_handler(RequestValidationError)(validation_error_handler)
    app.exception_handler(Exception)(unhandled_exception_handler)
    # Registered last: its catch-all route must not shadow the API.
    frontend_dist_dir = get_settings().frontend_dist_dir
    if frontend_dist_dir is not None:
        mount_frontend(app, frontend_dist_dir)
    return app


app = create_app()
