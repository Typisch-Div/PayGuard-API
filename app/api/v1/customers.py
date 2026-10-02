from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.schemas.error import ErrorResponse
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer",
    description="Creates a new customer with an initial nonnegative balance and unique email.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input parameters"},
        409: {"model": ErrorResponse, "description": "Customer with email already exists"},
    },
)
async def create_customer(
    customer_in: CustomerCreate,
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    return await CustomerService.create_customer(db=db, customer_in=customer_in)


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Get customer by ID",
    description="Retrieves customer details and available balance.",
    responses={
        404: {"model": ErrorResponse, "description": "Customer not found"},
    },
)
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    return await CustomerService.get_customer_by_id(db=db, customer_id=customer_id)
