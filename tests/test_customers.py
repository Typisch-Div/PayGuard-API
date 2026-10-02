import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_customer_success(client: AsyncClient):
    """Test successful customer creation with initial balance."""
    payload = {
        "name": "Alice Smith",
        "email": "alice@example.com",
        "currency": "USD",
        "balance": 150.50,
    }
    response = await client.post("/customers", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Alice Smith"
    assert data["email"] == "alice@example.com"
    assert data["currency"] == "USD"
    assert float(data["balance"]) == 150.50


@pytest.mark.asyncio
async def test_create_customer_duplicate_email(client: AsyncClient):
    """Test that creating a customer with an existing email returns 409 Conflict."""
    payload = {
        "name": "Bob Jones",
        "email": "bob@example.com",
        "currency": "USD",
        "balance": 100.00,
    }
    response1 = await client.post("/customers", json=payload)
    assert response1.status_code == 201

    response2 = await client.post("/customers", json=payload)
    assert response2.status_code == 409
    data = response2.json()
    assert data["error"]["code"] == "CUSTOMER_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_create_customer_invalid_balance(client: AsyncClient):
    """Test that negative initial balance is rejected by validation."""
    payload = {
        "name": "Charlie Brown",
        "email": "charlie@example.com",
        "currency": "USD",
        "balance": -50.00,
    }
    response = await client.post("/customers", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_customer_invalid_currency(client: AsyncClient):
    """Test that invalid currency code format is rejected."""
    payload = {
        "name": "Dave Wilson",
        "email": "dave@example.com",
        "currency": "INVALID",
        "balance": 50.00,
    }
    response = await client.post("/customers", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_customer_success(client: AsyncClient):
    """Test retrieving an existing customer by ID."""
    create_res = await client.post(
        "/customers",
        json={
            "name": "Eve Adams",
            "email": "eve@example.com",
            "currency": "EUR",
            "balance": 200.00,
        },
    )
    customer_id = create_res.json()["id"]

    get_res = await client.get(f"/customers/{customer_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == customer_id
    assert data["email"] == "eve@example.com"
    assert data["currency"] == "EUR"
    assert float(data["balance"]) == 200.00


@pytest.mark.asyncio
async def test_get_customer_not_found(client: AsyncClient):
    """Test retrieving a non-existent customer returns 404 Not Found."""
    random_id = str(uuid.uuid4())
    response = await client.get(f"/customers/{random_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "CUSTOMER_NOT_FOUND"
