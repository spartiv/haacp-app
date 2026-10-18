class AppError(Exception):
    """Raised by routers/dependencies to produce the API's unified error envelope."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class DomainError(Exception):
    """Base class for service-layer business-rule errors that map to a
    fixed HTTP status.

    Subclasses set `status_code` and `code` as class attributes plus a
    default `message`; the global handler registered in
    app/core/error_handlers.py converts any instance straight into the
    unified error envelope, so routers don't need a bespoke
    `except FooError: raise AppError(...)` block per error. Pass a string
    to the constructor to override the default message for one raise site
    (e.g. when the same error class serves more than one caller context).
    """

    status_code: int = 400
    code: str = "domain_error"
    message: str = "Request could not be processed"
    # Optional machine-readable context, returned as `error.details`.
    details: list[dict[str, str]] | None = None

    def __init__(
        self, message: str | None = None, *, details: list[dict[str, str]] | None = None
    ) -> None:
        if message is not None:
            self.message = message
        if details is not None:
            self.details = details
        super().__init__(self.message)


class NotFoundError(DomainError):
    """Base class for domain 'entity not found' errors."""

    status_code = 404
    code = "not_found"
    message = "Resource not found"
