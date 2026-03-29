"""
API key authentication for securing endpoints.
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import get_settings

# ── API Key Header ───────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI dependency that validates the API key from request headers.
    
    Usage:
        @app.get("/protected", dependencies=[Depends(verify_api_key)])
        def protected_route(): ...
    """
    settings = get_settings()

    # Allow all requests in debug mode if no key is provided
    if settings.DEBUG and api_key is None:
        return "debug-mode"

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide it via X-API-Key header.",
        )

    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key
