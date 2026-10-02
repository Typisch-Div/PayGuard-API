from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Service Health and Readiness Check",
    description="Returns API status and verifies database connectivity.",
)
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status,
    }
