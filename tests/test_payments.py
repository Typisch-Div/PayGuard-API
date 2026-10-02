import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_authorize_payment_success(client: AsyncClient):
    """Test successful payment authorization and balance deduction."""
    # 1. Create customer with 100.00 balance
    cust_res = await client.post(
        "/customers",
        json={"name": "John Doe", "email": "john@example.com", "currency": "USD", "balance": 100.00},
    )
    customer_id = cust_res.json()["id"]

    # 2. Authorize 40.00 payment
    auth_res = await client.post(
        "/payments/authorize",
        headers={"Idempotency-Key": "key-auth-001"},
        json={"customer_id": customer_id, "amount": 40.00, "currency": "USD"},
    )
    assert auth_res.status_code == 200
    payment = auth_res.json()
    assert payment["customer_id"] == customer_id
    assert float(payment["amount"]) == 40.00
    assert payment["status"] == "authorized"
    assert payment["decline_reason"] is None

    # 3. Verify customer balance updated to 60.00
    get_cust = await client.get(f"/customers/{customer_id}")
    assert float(get_cust.json()["balance"]) == 60.00


@pytest.mark.asyncio
async def test_authorize_payment_insufficient_funds(client: AsyncClient):
    """Test payment decline due to insufficient customer balance."""
    cust_res = await client.post(
        "/customers",
        json={"name": "Poor Pete", "email": "pete@example.com", "currency": "USD", "balance": 10.00},
    )
    customer_id = cust_res.json()["id"]

    # Attempt to authorize 50.00
    auth_res = await client.post(
        "/payments/authorize",
        headers={"Idempotency-Key": "key-auth-insufficient"},
        json={"customer_id": customer_id, "amount": 50.00, "currency": "USD"},
    )
    assert auth_res.status_code == 200
    payment = auth_res.json()
    assert payment["status"] == "declined"
    assert payment["decline_reason"] == "INSUFFICIENT_FUNDS"

    # Verify balance remains 10.00
    get_cust = await client.get(f"/customers/{customer_id}")
    assert float(get_cust.json()["balance"]) == 10.00


@pytest.mark.asyncio
async def test_authorize_payment_currency_mismatch(client: AsyncClient):
    """Test payment decline due to currency mismatch."""
    cust_res = await client.post(
        "/customers",
        json={"name": "Euro User", "email": "euro@example.com", "currency": "EUR", "balance": 100.00},
    )
    customer_id = cust_res.json()["id"]

    # Attempt to authorize in USD
    auth_res = await client.post(
        "/payments/authorize",
        headers={"Idempotency-Key": "key-currency-mismatch"},
        json={"customer_id": customer_id, "amount": 20.00, "currency": "USD"},
    )
    assert auth_res.status_code == 200
    payment = auth_res.json()
    assert payment["status"] == "declined"
    assert payment["decline_reason"] == "CURRENCY_MISMATCH"


@pytest.mark.asyncio
async def test_authorize_payment_unknown_customer(client: AsyncClient):
    """Test authorizing payment for non-existent customer returns 404."""
    random_id = str(uuid.uuid4())
    auth_res = await client.post(
        "/payments/authorize",
        headers={"Idempotency-Key": "key-unknown-cust"},
        json={"customer_id": random_id, "amount": 25.00, "currency": "USD"},
    )
    assert auth_res.status_code == 404
    data = auth_res.json()
    assert data["error"]["code"] == "CUSTOMER_NOT_FOUND"


@pytest.mark.asyncio
async def test_authorize_payment_invalid_amount(client: AsyncClient):
    """Test that zero or negative authorization amount is rejected by validation."""
    random_id = str(uuid.uuid4())
    auth_res = await client.post(
        "/payments/authorize",
        headers={"Idempotency-Key": "key-invalid-amt"},
        json={"customer_id": random_id, "amount": -10.00, "currency": "USD"},
    )
    assert auth_res.status_code == 422


@pytest.mark.asyncio
async def test_get_payment_success(client: AsyncClient):
    """Test retrieving payment details by payment ID."""
    cust_res = await client.post(
        "/customers",
        json={"name": "Fetch Test", "email": "fetch@example.com", "currency": "USD", "balance": 50.00},
    )
    customer_id = cust_res.json()["id"]

    auth_res = await client.post(
        "/payments/authorize",
        headers={"Idempotency-Key": "key-fetch-payment"},
        json={"customer_id": customer_id, "amount": 15.00, "currency": "USD"},
    )
    payment_id = auth_res.json()["id"]

    get_res = await client.get(f"/payments/{payment_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == payment_id
    assert data["customer_id"] == customer_id
    assert float(data["amount"]) == 15.00
    assert data["status"] == "authorized"


@pytest.mark.asyncio
async def test_get_payment_not_found(client: AsyncClient):
    """Test retrieving non-existent payment returns 404 Not Found."""
    random_id = str(uuid.uuid4())
    response = await client.get(f"/payments/{random_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PAYMENT_NOT_FOUND"
