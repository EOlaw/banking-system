# backend/app/middleware/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("banking-system")

async def error_handler(request: Request, exc):
    # Get request ID if available
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log error
    logger.error(
        f"Error: {request_id} - {request.method} {request.url.path} "
        f"- Status: {exc.status_code} - Detail: {exc.detail}"
    )
    
    # Return error response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )