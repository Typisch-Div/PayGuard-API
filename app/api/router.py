from fastapi import APIRouter

from app.api.v1.customers import router as customers_router
from app.api.v1.health import router as health_router
from app.api.v1.payments import router as payments_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(customers_router)
api_router.include_router(payments_router)
