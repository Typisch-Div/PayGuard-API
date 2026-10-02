from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CustomerNotFoundException,
    IdempotencyConflictException,
    PaymentNotFoundException,
)
from app.models.customer import Customer
from app.models.payment import Payment, PaymentDeclineReason, PaymentStatus
from app.schemas.payment import PaymentAuthorizeRequest


class PaymentService:
    @staticmethod
    async def authorize_payment(
        db: AsyncSession,
        idempotency_key: str,
        payment_in: PaymentAuthorizeRequest,
    ) -> Payment:
        """
        Authorize a payment against a customer's available balance with idempotency control.
        Uses PostgreSQL row-level locks (FOR UPDATE) and atomic conditional updates
        to guarantee race-condition safety and prevent overdraws under concurrency.
        """
        # Step 1: Idempotency pre-check
        existing_payment_stmt = select(Payment).where(
            Payment.customer_id == payment_in.customer_id,
            Payment.idempotency_key == idempotency_key,
        )
        result = await db.execute(existing_payment_stmt)
        existing_payment = result.scalar_one_or_none()

        if existing_payment:
            if (
                existing_payment.amount == payment_in.amount
                and existing_payment.currency == payment_in.currency
            ):
                return existing_payment
            else:
                raise IdempotencyConflictException(idempotency_key)

        try:
            # Step 2: Query customer with row lock
            customer_stmt = (
                select(Customer)
                .where(Customer.id == payment_in.customer_id)
                .with_for_update()
            )
            customer_result = await db.execute(customer_stmt)
            customer = customer_result.scalar_one_or_none()

            if not customer:
                raise CustomerNotFoundException(str(payment_in.customer_id))

            # Step 3: Currency validation check
            if customer.currency != payment_in.currency:
                payment = Payment(
                    customer_id=customer.id,
                    amount=payment_in.amount,
                    currency=payment_in.currency,
                    status=PaymentStatus.DECLINED.value,
                    idempotency_key=idempotency_key,
                    decline_reason=PaymentDeclineReason.CURRENCY_MISMATCH.value,
                )
                db.add(payment)
                await db.commit()
                await db.refresh(payment)
                return payment

            # Step 4: Atomic conditional balance deduction
            deduct_stmt = (
                update(Customer)
                .where(
                    Customer.id == customer.id,
                    Customer.balance >= payment_in.amount,
                )
                .values(balance=Customer.balance - payment_in.amount)
            )
            update_result = await db.execute(deduct_stmt)

            if update_result.rowcount == 0:
                # Balance was insufficient or deducted concurrently
                payment = Payment(
                    customer_id=customer.id,
                    amount=payment_in.amount,
                    currency=payment_in.currency,
                    status=PaymentStatus.DECLINED.value,
                    idempotency_key=idempotency_key,
                    decline_reason=PaymentDeclineReason.INSUFFICIENT_FUNDS.value,
                )
                db.add(payment)
                await db.commit()
                await db.refresh(payment)
                return payment

            # Step 5: Successful authorization
            payment = Payment(
                customer_id=customer.id,
                amount=payment_in.amount,
                currency=payment_in.currency,
                status=PaymentStatus.AUTHORIZED.value,
                idempotency_key=idempotency_key,
                decline_reason=None,
            )
            db.add(payment)
            await db.commit()
            await db.refresh(payment)
            return payment

        except IntegrityError:
            # Handle race condition on duplicate (customer_id, idempotency_key)
            await db.rollback()
            result = await db.execute(existing_payment_stmt)
            concurrent_payment = result.scalar_one_or_none()
            if concurrent_payment:
                if (
                    concurrent_payment.amount == payment_in.amount
                    and concurrent_payment.currency == payment_in.currency
                ):
                    return concurrent_payment
                else:
                    raise IdempotencyConflictException(idempotency_key)
            raise

    @staticmethod
    async def get_payment_by_id(db: AsyncSession, payment_id: UUID) -> Payment:
        """Retrieve a payment by UUID or raise PaymentNotFoundException."""
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await db.execute(stmt)
        payment = result.scalar_one_or_none()

        if not payment:
            raise PaymentNotFoundException(str(payment_id))

        return payment
