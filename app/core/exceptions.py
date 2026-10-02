from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger


class BaseAppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class CustomerNotFoundException(BaseAppException):
    def __init__(self, customer_id: str):
        super().__init__(
            message=f"Customer with ID '{customer_id}' was not found.",
            code="CUSTOMER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class PaymentNotFoundException(BaseAppException):
    def __init__(self, payment_id: str):
        super().__init__(
            message=f"Payment with ID '{payment_id}' was not found.",
            code="PAYMENT_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class CustomerAlreadyExistsException(BaseAppException):
    def __init__(self, email: str):
        super().__init__(
            message=f"Customer with email '{email}' already exists.",
            code="CUSTOMER_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT,
        )


class IdempotencyConflictException(BaseAppException):
    def __init__(self, idempotency_key: str):
        super().__init__(
            message=(
                f"Idempotency key '{idempotency_key}' was reused with a "
                "different request payload."
            ),
            code="IDEMPOTENCY_KEY_MISMATCH",
            status_code=status.HTTP_409_CONFLICT,
        )


class MissingIdempotencyKeyException(BaseAppException):
    def __init__(self):
        super().__init__(
            message="Idempotency-Key header is required for payment authorization.",
            code="MISSING_IDEMPOTENCY_KEY",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidCurrencyException(BaseAppException):
    def __init__(self, currency: str):
        super().__init__(
            message=f"Invalid ISO 4217 currency code: '{currency}'.",
            code="INVALID_CURRENCY",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """Handle custom application exceptions and format standard response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions to prevent stack trace leaks to client."""
    logger.error("Unhandled exception occurred: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
            }
        },
    )
