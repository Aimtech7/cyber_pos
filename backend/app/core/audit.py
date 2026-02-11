from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.audit import AuditLog
from ..models.user import User
import json


async def create_audit_log(
    db: Session,
    user: User,
    action: str,
    entity_type: str,
    entity_id: str,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """Create an audit log entry"""
    audit_log = AuditLog(
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def audit_action(action: str, entity_type: str):
    """Decorator for auditing actions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This is a placeholder for the decorator pattern
            # In practice, you'd extract user, db, and entity info from the function context
            result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator
