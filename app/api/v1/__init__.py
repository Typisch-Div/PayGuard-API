from app.api.v1.customers import router as customers_router
from app.api.v1.health import router as health_router
from app.api.v1.payments import router as payments_router

__all__ = ["customers_router", "payments_router", "health_router"]
