# backend/app/main.py
import time
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.api.v1.router import api_router
from app.middleware.error_handler import catch_exceptions_middleware
from app.middleware.logging import logging_middleware
from app.db.session import Base, engine

# Create database tables (in production, use alembic migrations instead)
# Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Banking System API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middlewares
app.middleware("http")(logging_middleware)
app.middleware("http")(catch_exceptions_middleware)

# Include API router
app.include_router(api_router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Banking System API",
        "documentation": "/api/docs",
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.PROJECT_VERSION,
    }

# Request processing time middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware to track request processing time
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

if __name__ == "__main__":
    # For development purposes only
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)