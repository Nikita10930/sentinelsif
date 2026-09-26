from .health import router as health_router
from .auth import router as auth_router
from .classify import router as classify_router
from .reports import router as reports_router
from .analytics import router as analytics_router

__all__ = [
    "health_router",
    "auth_router",
    "reports_router",
    "classify_router",
    "analytics_router",
]