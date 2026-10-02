import logging
import sys
from app.config import settings


def setup_logging() -> None:
    """Configure application logging without exposing sensitive data."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.getLogger("uvicorn.access").handlers = [logging.StreamHandler(sys.stdout)]


logger = logging.getLogger("payment_api")
