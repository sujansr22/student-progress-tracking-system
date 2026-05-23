import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User, UserRole, RefreshToken, PasswordResetToken

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def _hash_token(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def create_refresh_token(db: Session, user_id: int) -> str:
    """Issues a new refresh token. Revokes all prior active tokens for this user."""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({"is_revoked": True}, synchronize_session=False)

    plain = secrets.token_urlsafe(32)
    db.add(RefreshToken(
        user_id=user_id,
        token_hash=_hash_token(plain),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    ))
    db.commit()
    return plain


def verify_and_rotate_refresh_token(db: Session, plain: str) -> User:
    """Validates a refresh token, rotates it (revokes old, issues new), returns User."""
    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == _hash_token(plain),
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()

    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    record.is_revoked = True
    db.commit()
    return record.user


def revoke_refresh_token(db: Session, plain: str) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.token_hash == _hash_token(plain)
    ).update({"is_revoked": True}, synchronize_session=False)
    db.commit()


def create_password_reset_token(db: Session, user_id: int) -> str:
    """Creates a 1-hour password reset token. Invalidates prior tokens."""
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.is_used == False
    ).update({"is_used": True}, synchronize_session=False)

    plain = secrets.token_urlsafe(32)
    db.add(PasswordResetToken(
        user_id=user_id,
        token_hash=_hash_token(plain),
        expires_at=datetime.utcnow() + timedelta(hours=1)
    ))
    db.commit()
    return plain


def consume_password_reset_token(db: Session, plain: str) -> User:
    """Validates and marks a reset token as used. Returns the User."""
    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == _hash_token(plain),
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()

    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    record.is_used = True
    db.commit()
    return record.user


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        logger.warning("JWT decode failed — invalid or expired token")
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def require_roles(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required permissions to access this resource"
            )
        return current_user
    return role_checker
