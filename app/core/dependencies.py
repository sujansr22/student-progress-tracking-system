from datetime import date, timedelta
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import User, UserRole, Subscription

GRACE_PERIOD_DAYS = 7


def require_active_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Blocks write access when a school's subscription has expired beyond the grace period.
    SUPER_ADMIN is never blocked. Read-only routes should NOT use this dependency.

    Grace period: 7 days after end_date before access is locked.
    """
    if current_user.role in (UserRole.SUPER_ADMIN, UserRole.STUDENT):
        return current_user

    if not current_user.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No institution assigned to this account")

    today = date.today()
    grace_cutoff = today - timedelta(days=GRACE_PERIOD_DAYS)

    subscription = db.query(Subscription).filter(
        Subscription.institution_id == current_user.institution_id,
        Subscription.is_active == True,
        Subscription.end_date >= grace_cutoff,
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "Your institution's subscription has expired. "
                "Read access remains active. Contact support to renew."
            ),
        )

    return current_user
