# backend/app/db/repositories/audit.py
from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models.audit import AuditLog, AuditAction
from .base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog, None, None]):
    """Repository for AuditLog model operations."""

    def __init__(self):
        super().__init__(AuditLog)
    
    def log_action(
        self,
        db: Session,
        *,
        action: AuditAction,
        entity_type: str,
        entity_id: int = None,
        user_id: int = None,
        data: dict = None,
        ip_address: str = None,
    ) -> AuditLog:
        """
        Log an action in the audit log.
        
        Args:
            db: Database session
            action: Action type
            entity_type: Entity type
            entity_id: Entity ID
            user_id: User ID
            data: Additional data
            ip_address: IP address
            
        Returns:
            Created audit log entry
        """
        audit_log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            data=data,
            ip_address=ip_address,
        )
        db.add(audit_log)
        db.flush()
        return audit_log
    
    def get_user_audit_logs(
        self,
        db: Session,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime = None,
        end_date: datetime = None,
        action: AuditAction = None,
        entity_type: str = None,
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of logs to skip
            limit: Maximum number of logs to return
            start_date: Filter by start date
            end_date: Filter by end date
            action: Filter by action
            entity_type: Filter by entity type
            
        Returns:
            List of audit logs
        """
        query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
        
        # Apply filters
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
            
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
            
        if action:
            query = query.filter(AuditLog.action == action)
            
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        
        # Order by creation date, newest first
        query = query.order_by(desc(AuditLog.created_at))
        
        return query.offset(skip).limit(limit).all()
    
    def get_entity_audit_logs(
        self,
        db: Session,
        *,
        entity_type: str,
        entity_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime = None,
        end_date: datetime = None,
        action: AuditAction = None,
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific entity.
        
        Args:
            db: Database session
            entity_type: Entity type
            entity_id: Entity ID
            skip: Number of logs to skip
            limit: Maximum number of logs to return
            start_date: Filter by start date
            end_date: Filter by end date
            action: Filter by action
            
        Returns:
            List of audit logs
        """
        query = db.query(AuditLog).filter(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
        )
        
        # Apply filters
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
            
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
            
        if action:
            query = query.filter(AuditLog.action == action)
        
        # Order by creation date, newest first
        query = query.order_by(desc(AuditLog.created_at))
        
        return query.offset(skip).limit(limit).all()
    
    def get_security_audit_logs(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        days: int = 30,
    ) -> List[AuditLog]:
        """
        Get security-related audit logs.
        
        Args:
            db: Database session
            skip: Number of logs to skip
            limit: Maximum number of logs to return
            days: Number of days to include
            
        Returns:
            List of security audit logs
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # Security-related actions
        security_actions = [
            AuditAction.LOGIN,
            AuditAction.LOGOUT,
        ]
        
        query = db.query(AuditLog).filter(
            AuditLog.created_at >= start_date,
            AuditLog.action.in_(security_actions),
        )
        
        # Order by creation date, newest first
        query = query.order_by(desc(AuditLog.created_at))
        
        return query.offset(skip).limit(limit).all()