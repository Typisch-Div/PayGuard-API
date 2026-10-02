from datetime import datetime
from decimal import Decimal
import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Customer full name")
    email: EmailStr = Field(..., description="Customer unique email address")
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="3-letter ISO 4217 currency code",
    )
    balance: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        decimal_places=2,
        description="Initial balance (nonnegative decimal with 2 decimal places)",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", v_upper):
            raise ValueError("Currency must be a valid 3-letter ISO 4217 code")
        return v_upper

    @field_validator("balance")
    @classmethod
    def validate_balance_precision(cls, v: Decimal) -> Decimal:
        if v.as_tuple().exponent < -2:
            raise ValueError("Balance cannot have more than 2 decimal places")
        return v


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    currency: str
    balance: Decimal
    created_at: datetime
    updated_at: datetime
