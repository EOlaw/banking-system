# backend/app/db/repositories/__init__.py
from .users import UserRepository
from .accounts import AccountRepository
from .transactions import TransactionRepository
from .audit import AuditLogRepository

# Create repository instances
user_repository = UserRepository()
account_repository = AccountRepository()
transaction_repository = TransactionRepository()
audit_repository = AuditLogRepository()

# Export repository instances for convenient importing
__all__ = [
    "user_repository",
    "account_repository",
    "transaction_repository",
    "audit_repository",
]