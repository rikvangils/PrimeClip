from fastapi import FastAPI, HTTPException

from app.config import get_settings
from app.review.api import router as review_router

app = FastAPI(title="PeanutClip AutoFlow API", version="0.1.0")
app.include_router(review_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["system"])
def health_ready() -> dict[str, str]:
    """Readiness probe: verifies all required integration credentials are set."""
    try:
        get_settings().validate_required_integrations()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ready"}
