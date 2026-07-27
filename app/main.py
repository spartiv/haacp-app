from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_handlers import (
    app_error_handler,
    http_exception_handler,
    not_found_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.errors import AppError, NotFoundError
from app.core.logging_config import configure_logging
from app.routers.v1 import api_router


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Polton HACCP API")
    app.include_router(api_router)
    app.exception_handler(AppError)(app_error_handler)
    app.exception_handler(NotFoundError)(not_found_handler)
    app.exception_handler(StarletteHTTPException)(http_exception_handler)
    app.exception_handler(RequestValidationError)(validation_error_handler)
    app.exception_handler(Exception)(unhandled_exception_handler)
    return app


app = create_app()
