class AppError(Exception):
    """Raised by routers/dependencies to produce the API's unified error envelope."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundError(Exception):
    """Base class for domain 'entity not found' errors.

    Subclasses set `code` and `message` once as class attributes; the
    global handler registered in app/core/error_handlers.py turns any
    instance straight into the unified 404 error envelope, so routers
    don't need a bespoke `except FooNotFoundError` block per entity.
    """

    code: str = "not_found"
    message: str = "Resource not found"
