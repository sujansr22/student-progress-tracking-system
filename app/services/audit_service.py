from sqlalchemy.orm import Session
from app.models.models import AuditLog

from typing import Optional

def log_action(db: Session, user_id: int, action: str, entity: str, action_type: str = "CREATE", ip_address: Optional[str] = None):
    """
    Utility to record an audit log entry.
    """
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        action_type=action_type,
        ip_address=ip_address
    )
    db.add(audit_entry)
    # Note: We rely on the caller to commit if this is part of a larger transaction.
    # If it's a standalone log, the caller must call db.commit().
