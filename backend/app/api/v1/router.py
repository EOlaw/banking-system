# backend/app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.auth.routes import router as auth_router
from app.api.v1.users.routes import router as users_router
from app.api.v1.accounts.routes import router as accounts_router
from app.api.v1.transactions.routes import router as transactions_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["Transactions"])