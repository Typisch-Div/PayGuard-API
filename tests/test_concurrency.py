import asyncio
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_concurrent_payments_prevent_overdraw(client: AsyncClient):
    """
    Test that concurrent authorization requests do not overdraw the customer balance.
    Customer balance: 100.00
    3 concurrent requests of 40.00 each with unique idempotency keys.
    Exactly 2 requests should be authorized (80.00 total), and 1 should be declined (INSUFFICIENT_FUNDS).
    Final balance must be exactly 20.00.
    """
    cust_res = await client.post(
        "/customers",
        json={"name": "Race Tester", "email": "racer@example.com", "currency": "USD", "balance": 100.00},
    )
    customer_id = cust_res.json()["id"]

    async def make_payment_request(key: str):
        return await client.post(
            "/payments/authorize",
            headers={"Idempotency-Key": key},
            json={"customer_id": customer_id, "amount": 40.00, "currency": "USD"},
        )

    # Launch 3 concurrent requests simultaneously
    results = await asyncio.gather(
        make_payment_request("concurrent-key-1"),
        make_payment_request("concurrent-key-2"),
        make_payment_request("concurrent-key-3"),
    )

    statuses = [res.json()["status"] for res in results]
    authorized_count = statuses.count("authorized")
    declined_count = statuses.count("declined")

    assert authorized_count == 2
    assert declined_count == 1

    # Verify final customer balance is 20.00
    cust_check = await client.get(f"/customers/{customer_id}")
    assert float(cust_check.json()["balance"]) == 20.00
