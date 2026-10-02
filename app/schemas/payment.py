from datetime import datetime
from decimal import Decimal
import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentAuthorizeRequest(BaseModel):
    customer_id: UUID = Field(..., description="ID of the customer requesting authorization")
    amount: Decimal = Field(
        ...,
        gt=Decimal("0.00"),
        decimal_places=2,
        description="Payment amount (positive decimal with up to 2 decimal places)",
    )
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="3-letter ISO 4217 currency code",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", v_upper):
            raise ValueError("Currency must be a valid 3-letter ISO 4217 code")
        return v_upper

    @field_validator("amount")
    @classmethod
    def validate_amount_precision(cls, v: Decimal) -> Decimal:
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    amount: Decimal
    currency: str
    status: str
    idempotency_key: str
    decline_reason: Optional[str] = None
    created_at: datetime
