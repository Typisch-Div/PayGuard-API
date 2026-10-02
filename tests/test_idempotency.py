import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_missing_idempotency_key(client: AsyncClient):
    """Test that missing Idempotency-Key header returns 400 Bad Request."""
    cust_res = await client.post(
        "/customers",
        json={"name": "No Key", "email": "nokey@example.com", "currency": "USD", "balance": 100.00},
    )
    customer_id = cust_res.json()["id"]

    response = await client.post(
        "/payments/authorize",
        json={"customer_id": customer_id, "amount": 20.00, "currency": "USD"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"


@pytest.mark.asyncio
async def test_repeated_idempotency_same_payload(client: AsyncClient):
    """Test that repeating request with identical payload returns saved payment without double-deduction."""
    cust_res = await client.post(
        "/customers",
        json={"name": "Idempotent User", "email": "idemp@example.com", "currency": "USD", "balance": 100.00},
    )
    customer_id = cust_res.json()["id"]
    payload = {"customer_id": customer_id, "amount": 30.00, "currency": "USD"}
    key = "unique-key-12345"

    # First attempt
    res1 = await client.post("/payments/authorize", headers={"Idempotency-Key": key}, json=payload)
    assert res1.status_code == 200
    payment1 = res1.json()

    # Second attempt (same key & payload)
    res2 = await client.post("/payments/authorize", headers={"Idempotency-Key": key}, json=payload)
    assert res2.status_code == 200
    payment2 = res2.json()

    # Must return exact same payment ID
    assert payment1["id"] == payment2["id"]
    assert payment1["status"] == payment2["status"]

    # Balance must only have been deducted ONCE (100.00 - 30.00 = 70.00)
    cust_check = await client.get(f"/customers/{customer_id}")
    assert float(cust_check.json()["balance"]) == 70.00


@pytest.mark.asyncio
async def test_reused_idempotency_key_different_payload(client: AsyncClient):
    """Test that reusing an idempotency key with a different payload returns 409 Conflict."""
    cust_res = await client.post(
        "/customers",
        json={"name": "Conflict User", "email": "conflict@example.com", "currency": "USD", "balance": 100.00},
    )
    customer_id = cust_res.json()["id"]
    key = "shared-key-999"

    # First authorization for 25.00
    res1 = await client.post(
        "/payments/authorize",
        headers={"Idempotency-Key": key},
        json={"customer_id": customer_id, "amount": 25.00, "currency": "USD"},
    )
    assert res1.status_code == 200

    # Second authorization reusing same key for DIFFERENT amount (50.00)
    res2 = await client.post(
        "/payments/authorize",
        headers={"Idempotency-Key": key},
        json={"customer_id": customer_id, "amount": 50.00, "currency": "USD"},
    )
    assert res2.status_code == 409
    data = res2.json()
    assert data["error"]["code"] == "IDEMPOTENCY_KEY_MISMATCH"

    # Balance must reflect only the first authorized payment (75.00)
    cust_check = await client.get(f"/customers/{customer_id}")
    assert float(cust_check.json()["balance"]) == 75.00
