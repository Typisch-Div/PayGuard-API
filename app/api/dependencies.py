from typing import Optional
from fastapi import Header

from app.core.exceptions import MissingIdempotencyKeyException


async def get_idempotency_key(
    idempotency_key: Optional[str] = Header(
        None,
        alias="Idempotency-Key",
        description="Unique string to enforce payment authorization idempotency",
    ),
) -> str:
    """Validate and return the required Idempotency-Key header."""
    if not idempotency_key or not idempotency_key.strip():
        raise MissingIdempotencyKeyException()
    return idempotency_key.strip()
