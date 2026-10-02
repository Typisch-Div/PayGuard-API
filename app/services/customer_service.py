from uuid import UUID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CustomerAlreadyExistsException, CustomerNotFoundException
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate


class CustomerService:
    @staticmethod
    async def create_customer(db: AsyncSession, customer_in: CustomerCreate) -> Customer:
        """Create a new customer with initial balance."""
        stmt = select(Customer).where(Customer.email == customer_in.email)
        result = await db.execute(stmt)
        existing_customer = result.scalar_one_or_none()

        if existing_customer:
            raise CustomerAlreadyExistsException(customer_in.email)

        customer = Customer(
            name=customer_in.name,
            email=customer_in.email,
            currency=customer_in.currency,
            balance=customer_in.balance,
        )

        db.add(customer)
        try:
            await db.commit()
            await db.refresh(customer)
            return customer
        except IntegrityError:
            await db.rollback()
            raise CustomerAlreadyExistsException(customer_in.email)

    @staticmethod
    async def get_customer_by_id(db: AsyncSession, customer_id: UUID) -> Customer:
        """Retrieve a customer by UUID or raise CustomerNotFoundException."""
        stmt = select(Customer).where(Customer.id == customer_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            raise CustomerNotFoundException(str(customer_id))

        return customer
