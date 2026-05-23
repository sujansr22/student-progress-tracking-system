from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.auth import require_roles
from app.core.database import get_db
from app.models.models import User, UserRole, Subscription, Institution
from app.schemas.schemas import SubscriptionCreate, SubscriptionResponse, SubscriptionStatusResponse

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

GRACE_PERIOD_DAYS = 7


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    sub: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """SUPER_ADMIN creates a subscription for an institution."""
    institution = db.query(Institution).filter(Institution.id == sub.institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    existing = db.query(Subscription).filter(
        Subscription.institution_id == sub.institution_id,
        Subscription.is_active == True,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institution already has an active subscription. Use /renew to extend it.",
        )

    new_sub = Subscription(institution_id=sub.institution_id, is_active=True, end_date=sub.end_date)
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub


@router.put("/{institution_id}/renew", response_model=SubscriptionResponse)
def renew_subscription(
    institution_id: int,
    days: int = Query(365, ge=1, le=1095, description="Number of days to extend"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """
    Extend a school's subscription by N days.
    If already expired: starts from today.
    If still active: extends from current end_date.
    """
    sub = db.query(Subscription).filter(
        Subscription.institution_id == institution_id,
        Subscription.is_active == True,
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found for this institution")

    base = max(sub.end_date, date.today())
    sub.end_date = base + timedelta(days=days)
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/", response_model=List[SubscriptionResponse])
def list_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """SUPER_ADMIN view of all subscriptions across all institutions."""
    return db.query(Subscription).offset(skip).limit(limit).all()


@router.get("/status", response_model=SubscriptionStatusResponse)
def my_subscription_status(
    institution_id: Optional[int] = Query(None, description="SUPER_ADMIN only: query any institution"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Returns subscription status for an institution.
    SCHOOL_ADMIN always sees their own institution.
    SUPER_ADMIN can pass ?institution_id= to query any institution.
    """
    target_id = institution_id if current_user.role == UserRole.SUPER_ADMIN else current_user.institution_id

    if not target_id:
        raise HTTPException(status_code=400, detail="institution_id required")

    institution = db.query(Institution).filter(Institution.id == target_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    sub = db.query(Subscription).filter(
        Subscription.institution_id == target_id,
        Subscription.is_active == True,
    ).first()

    if not sub:
        raise HTTPException(
            status_code=404,
            detail="No active subscription found for this institution",
        )

    today = date.today()
    days_remaining = (sub.end_date - today).days
    is_in_grace_period = days_remaining < 0 and days_remaining >= -GRACE_PERIOD_DAYS

    return SubscriptionStatusResponse(
        institution_id=target_id,
        institution_name=institution.name,
        is_active=sub.is_active,
        end_date=sub.end_date,
        days_remaining=max(days_remaining, 0),
        is_in_grace_period=is_in_grace_period,
    )
