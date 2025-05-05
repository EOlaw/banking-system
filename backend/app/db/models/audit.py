# backend/app/db/models/audit.py
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Enum
import enum

from ..base import BaseModel

class AuditAction(enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"

class AuditLog(BaseModel):
    """Audit log model for tracking all important actions"""
    __tablename__ = "audit_logs"
    
    action = Column(Enum(AuditAction), nullable=False)
    entity_type = Column(String(50), nullable=False)  # e.g., "user", "account", "transaction"
    entity_id = Column(Integer, nullable=True)
    data = Column(JSON, nullable=True)  # Details of the action
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6 address
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for system actions
    
    def __repr__(self):
        return f"<AuditLog {self.action.value} {self.entity_type} {self.entity_id}>"