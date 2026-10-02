# Mini Payment Authorization API

A production-minded, high-performance REST API built with **Python 3.12**, **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.0 (asyncio)**, **Alembic**, **pytest**, and **Docker Compose**.

This service allows merchants to authorize payments against customer balances while preventing duplicate charges (idempotency), rejecting overdraws/invalid requests, enforcing concurrency control via PostgreSQL row locks, and maintaining an audit trail.

---

## Features

- **Asynchronous & Non-blocking**: Full `async/await` database pipeline using SQLAlchemy 2.0 and `asyncpg`.
- **Idempotency Control**: Header-based idempotency (`Idempotency-Key`). Re-sending identical payloads returns saved payments; reusing keys with different payloads returns `409 Conflict`.
- **Atomic Balance Operations & Race-Condition Safety**: Protects against double-spending and overdraws under heavy concurrent requests using PostgreSQL `SELECT ... FOR UPDATE` row locks and database unique constraints.
- **Financial Precision**: All monetary values use Python's `Decimal` type mapped to PostgreSQL `NUMERIC(12, 2)` columns, accompanied by database check constraints (`balance >= 0`, `amount > 0`).
- **Structured Error Handling**: Standardized JSON error response schema that hides internal stack traces and secrets from API clients.
- **Database Migrations**: Alembic setup supporting async schema migrations.
- **Docker Ready**: One-command local development setup with PostgreSQL health checks and automated migrations on startup.

---

## Tech Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI (Pydantic v2)
- **Database**: PostgreSQL 16
- **ORM & Driver**: SQLAlchemy 2.0 ORM + `asyncpg`
- **Migrations**: Alembic
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`
- **Containerization**: Docker & Docker Compose

---

## Project Structure

```
payment_authorization_api/
├── app/
│   ├── main.py                  # FastAPI application setup & lifecycle
│   ├── config.py                # Environment configuration (Pydantic Settings)
│   ├── api/
│   │   ├── router.py            # Central router registry
│   │   ├── dependencies.py      # Request header & DB dependencies
│   │   └── v1/
│   │       ├── customers.py     # Customer management endpoints
│   │       ├── payments.py      # Payment authorization endpoints
│   │       └── health.py        # Health & DB readiness check
│   ├── core/
│   │   ├── exceptions.py        # Custom exceptions & global handlers
│   │   └── logging.py           # Logging setup
│   ├── db/
│   │   ├── session.py           # Async engine & session factory
│   │   └── base.py              # Declarative base model
│   ├── models/
│   │   ├── customer.py          # Customer SQLAlchemy model
│   │   └── payment.py           # Payment SQLAlchemy model
│   ├── schemas/
│   │   ├── customer.py          # Customer Pydantic schemas
│   │   ├── payment.py           # Payment Pydantic schemas
│   │   └── error.py             # Error response schemas
│   └── services/
│       ├── customer_service.py  # Customer business logic
│       └── payment_service.py   # Payment authorization & concurrency engine
├── alembic/
│   ├── env.py                   # Migration environment configuration
│   └── versions/
│       └── 001_initial_schema.py# Initial DB schema migration
├── tests/
│   ├── conftest.py              # Pytest fixtures & async test client
│   ├── test_customers.py        # Customer endpoint unit tests
│   ├── test_payments.py         # Payment endpoint unit tests
│   ├── test_idempotency.py      # Idempotency behavior tests
│   ├── test_concurrency.py      # Concurrency & race condition tests
│   └── test_health.py           # Health endpoint tests
├── scripts/
│   └── start.sh                 # Docker container startup script
├── .env.example                 # Example environment variables
├── Dockerfile                   # Application container definition
├── docker-compose.yml           # Docker Compose orchestrator
├── pyproject.toml               # Python project configuration
├── requirements.txt             # Python dependency manifest
└── README.md                    # Project documentation
```

---

## Quickstart with Docker Compose

### Prerequisites
- Docker Engine 24+
- Docker Compose v2+

### Start the Service

1. Clone or navigate to the project root directory:
   ```bash
   cd payment_authorization_api
   ```

2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. Build and launch the containers:
   ```bash
   docker compose up --build
   ```

The FastAPI application will automatically apply database migrations on startup and begin serving requests at `http://localhost:8000`.

OpenAPI documentation is available at `http://localhost:8000/docs`.

---

## Running Tests

### Running Tests Locally (Virtual Environment)

1. Create and activate a Python 3.12 virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute pytest:
   ```bash
   pytest -v
   ```

### Running Tests in Docker Container

Run tests directly inside the running API container:
```bash
docker compose exec api pytest -v
```

---

## Running Database Migrations Manually

To run or generate migrations using Alembic:

```bash
# Apply migrations to latest head
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Create a new autogenerated migration
alembic revision --autogenerate -m "Add new column"
```

---

## API Endpoints & Example Curl Requests

### 1. Health Check
`GET /health`

**Request:**
```bash
curl -X GET http://localhost:8000/health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "database": "healthy"
}
```

---

### 2. Create Customer
`POST /customers`

**Request:**
```bash
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Storefront",
    "email": "acme@example.com",
    "currency": "USD",
    "balance": 500.00
  }'
```

**Response (201 Created):**
```json
{
  "id": "a3b1c2d4-e5f6-7890-abcd-ef1234567890",
  "name": "Acme Storefront",
  "email": "acme@example.com",
  "currency": "USD",
  "balance": "500.00",
  "created_at": "2026-10-02T12:00:00.000000+00:00",
  "updated_at": "2026-10-02T12:00:00.000000+00:00"
}
```

---

### 3. Get Customer Details
`GET /customers/{customer_id}`

**Request:**
```bash
curl -X GET http://localhost:8000/customers/a3b1c2d4-e5f6-7890-abcd-ef1234567890
```

**Response (200 OK):**
```json
{
  "id": "a3b1c2d4-e5f6-7890-abcd-ef1234567890",
  "name": "Acme Storefront",
  "email": "acme@example.com",
  "currency": "USD",
  "balance": "500.00",
  "created_at": "2026-10-02T12:00:00.000000+00:00",
  "updated_at": "2026-10-02T12:00:00.000000+00:00"
}
```

---

### 4. Authorize Payment
`POST /payments/authorize`

Requires an `Idempotency-Key` header.

**Request:**
```bash
curl -X POST http://localhost:8000/payments/authorize \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: key_order_1001" \
  -d '{
    "customer_id": "a3b1c2d4-e5f6-7890-abcd-ef1234567890",
    "amount": 75.50,
    "currency": "USD"
  }'
```

**Response (200 OK - Authorized):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d4e5",
  "customer_id": "a3b1c2d4-e5f6-7890-abcd-ef1234567890",
  "amount": "75.50",
  "currency": "USD",
  "status": "authorized",
  "idempotency_key": "key_order_1001",
  "decline_reason": null,
  "created_at": "2026-10-02T12:05:00.000000+00:00"
}
```

**Response (200 OK - Declined due to insufficient funds):**
```json
{
  "id": "e88bc10a-12dd-4372-b567-1f02b2c3d4e6",
  "customer_id": "a3b1c2d4-e5f6-7890-abcd-ef1234567890",
  "amount": "9999.00",
  "currency": "USD",
  "status": "declined",
  "idempotency_key": "key_order_1002",
  "decline_reason": "INSUFFICIENT_FUNDS",
  "created_at": "2026-10-02T12:06:00.000000+00:00"
}
```

---

### 5. Idempotency Key Reuse (409 Conflict)

Reusing the key `key_order_1001` with a different amount or currency:

**Request:**
```bash
curl -X POST http://localhost:8000/payments/authorize \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: key_order_1001" \
  -d '{
    "customer_id": "a3b1c2d4-e5f6-7890-abcd-ef1234567890",
    "amount": 100.00,
    "currency": "USD"
  }'
```

**Response (409 Conflict):**
```json
{
  "error": {
    "code": "IDEMPOTENCY_KEY_MISMATCH",
    "message": "Idempotency key 'key_order_1001' was reused with a different request payload.",
    "details": {}
  }
}
```

---

### 6. Get Payment Details
`GET /payments/{payment_id}`

**Request:**
```bash
curl -X GET http://localhost:8000/payments/f47ac10b-58cc-4372-a567-0e02b2c3d4e5
```

**Response (200 OK):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d4e5",
  "customer_id": "a3b1c2d4-e5f6-7890-abcd-ef1234567890",
  "amount": "75.50",
  "currency": "USD",
  "status": "authorized",
  "idempotency_key": "key_order_1001",
  "decline_reason": null,
  "created_at": "2026-10-02T12:05:00.000000+00:00"
}
```

---

## Design Decisions & Correctness

1. **Row-Level Locking (`FOR UPDATE`)**:
   - During payment authorization, `Customer` rows are queried using `SELECT ... FOR UPDATE`. This ensures concurrent authorization attempts on the same customer execute serially in PostgreSQL, preventing double-spending and negative balances.
2. **Idempotency Guard**:
   - Payments table enforces `UNIQUE (customer_id, idempotency_key)`. If simultaneous requests with the same key pass initial lookup, PostgreSQL unique constraint catches it and triggers rollback + lookup fallback.
3. **Security & PCI-DSS Scope**:
   - No payment card data (PAN, CVV, PIN, expiration) or banking credentials are collected, stored, or processed by this API. It purely manages authorization against internal merchant customer balances.
