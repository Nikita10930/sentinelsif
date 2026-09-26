from fastapi import APIRouter
from ..schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend service status."""
    return {"status": "ok", "service": "SentinelSIF"}
