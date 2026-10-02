from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_idempotency_key
from app.db.session import get_db
from app.schemas.error import ErrorResponse
from app.schemas.payment import PaymentAuthorizeRequest, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/authorize",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Authorize a payment",
    description=(
        "Authorize a payment against a customer's available balance. "
        "Requires a valid 'Idempotency-Key' header. Repeating requests with the same key "
        "and payload returns the original payment. Reusing a key with a different payload "
        "returns HTTP 409 Conflict."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid payload or missing Idempotency-Key header"},
        404: {"model": ErrorResponse, "description": "Customer not found"},
        409: {"model": ErrorResponse, "description": "Idempotency key reuse with mismatched payload"},
    },
)
async def authorize_payment(
    payment_in: PaymentAuthorizeRequest,
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    return await PaymentService.authorize_payment(
        db=db,
        idempotency_key=idempotency_key,
        payment_in=payment_in,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get payment by ID",
    description="Retrieves a payment record and its authorization status.",
    responses={
        404: {"model": ErrorResponse, "description": "Payment not found"},
    },
)
async def get_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    return await PaymentService.get_payment_by_id(db=db, payment_id=payment_id)
