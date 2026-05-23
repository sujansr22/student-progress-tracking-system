import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.core.auth import (
    verify_password, create_access_token, get_password_hash,
    create_refresh_token, verify_and_rotate_refresh_token,
    revoke_refresh_token, create_password_reset_token, consume_password_reset_token,
)
from app.core.config import settings
from app.core.email import send_password_reset_email
from app.core.limiter import limiter
from app.models.models import User, UserRole, RefreshToken, Student
from app.schemas.schemas import Token, UserRegister, RefreshRequest, ForgotPasswordRequest, ResetPasswordRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=UserRole.INSTRUCTOR,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "email": new_user.email, "role": new_user.role}


@router.post("/student-register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def student_register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Students self-register using their enrolled email.
    The email must match an existing active Student record — school admins control enrolment.
    """
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    student = db.query(Student).filter(
        Student.email == user_data.email,
        Student.is_active == True,
        Student.user_id == None,
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No student record found for this email. Contact your school to verify your enrollment.",
        )

    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=UserRole.STUDENT,
        institution_id=student.institution_id,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    student.user_id = new_user.id
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "email": new_user.email, "role": new_user.role}


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username, User.is_active == True).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "institution_id": user.institution_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(db, user.id)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@router.post("/refresh", response_model=Token)
async def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    user = verify_and_rotate_refresh_token(db, body.refresh_token)

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "institution_id": user.institution_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    new_refresh_token = create_refresh_token(db, user.id)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": new_refresh_token}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    """Revoke the refresh token so it can never be reused."""
    revoke_refresh_token(db, body.refresh_token)
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Sends a password reset link. Always returns 200 — never reveals whether the email exists.
    In development (no SMTP configured), the token is printed to server logs.
    """
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if user:
        plain_token = create_password_reset_token(db, user.id)
        await send_password_reset_email(user.email, plain_token)

        if settings.ENVIRONMENT == "development":
            logger.info("DEV reset token for %s: %s", user.email, plain_token)

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Consume a reset token and set a new password. Revokes all active sessions."""
    user = consume_password_reset_token(db, body.token)

    user.hashed_password = get_password_hash(body.new_password)

    # Force re-login on all devices after password change
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.is_revoked == False,
    ).update({"is_revoked": True}, synchronize_session=False)

    db.commit()
    return {"message": "Password reset successful. Please log in again."}
