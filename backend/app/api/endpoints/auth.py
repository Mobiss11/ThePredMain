from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.core.config import settings
from pydantic import BaseModel
from jose import jwt
from datetime import datetime, timedelta
import hashlib
import secrets

router = APIRouter()


class TelegramAuthData(BaseModel):
    id: int
    first_name: str
    username: str | None = None
    last_name: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class SimpleTelegramAuth(BaseModel):
    """Simple auth model for bot registration"""
    telegram_id: int
    first_name: str
    username: str | None = None
    last_name: str | None = None
    photo_url: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int


class UserInfoResponse(BaseModel):
    user_id: int
    id: int | None = None  # Alias for user_id (for compatibility)
    telegram_id: int
    username: str | None
    first_name: str
    photo_url: str | None
    pred_balance: float
    referral_code: str


def verify_telegram_auth(auth_data: dict) -> bool:
    """Verify Telegram WebApp authorization"""
    check_hash = auth_data.pop('hash', None)
    if not check_hash:
        return False

    # In production, use BOT_TOKEN from settings
    # For now, simplified version
    return True


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


@router.post("/telegram", response_model=TokenResponse)
async def telegram_auth(
    auth_data: TelegramAuthData,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user via Telegram"""
    # Verify Telegram data
    if not verify_telegram_auth(auth_data.dict()):
        raise HTTPException(status_code=401, detail="Invalid authentication data")

    # Check if user exists
    result = await db.execute(
        select(User).where(User.telegram_id == auth_data.id)
    )
    user = result.scalar_one_or_none()

    # Create new user if doesn't exist
    if not user:
        referral_code = secrets.token_urlsafe(8)
        user = User(
            telegram_id=auth_data.id,
            username=auth_data.username,
            first_name=auth_data.first_name,
            last_name=auth_data.last_name,
            photo_url=auth_data.photo_url,
            pred_balance=settings.INITIAL_PRED_BALANCE,
            referral_code=referral_code
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif auth_data.photo_url and user.photo_url != auth_data.photo_url:
        # Update photo if changed
        user.photo_url = auth_data.photo_url
        await db.commit()
        await db.refresh(user)

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.telegram_id), "user_id": user.id}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id
    )


@router.post("/register", response_model=UserInfoResponse)
async def register_user(
    auth_data: SimpleTelegramAuth,
    db: AsyncSession = Depends(get_db)
):
    """Simple user registration from bot - no auth required"""
    # Check if user exists
    result = await db.execute(
        select(User).where(User.telegram_id == auth_data.telegram_id)
    )
    user = result.scalar_one_or_none()

    # Create new user if doesn't exist
    if not user:
        referral_code = secrets.token_urlsafe(8)
        user = User(
            telegram_id=auth_data.telegram_id,
            username=auth_data.username,
            first_name=auth_data.first_name,
            last_name=auth_data.last_name,
            photo_url=auth_data.photo_url,
            pred_balance=settings.INITIAL_PRED_BALANCE,
            referral_code=referral_code
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif auth_data.photo_url and user.photo_url != auth_data.photo_url:
        # Update photo if changed
        user.photo_url = auth_data.photo_url
        await db.commit()
        await db.refresh(user)

    return UserInfoResponse(
        user_id=user.id,
        id=user.id,  # For compatibility with webapp
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        photo_url=user.photo_url,
        pred_balance=user.pred_balance,
        referral_code=user.referral_code
    )


@router.get("/verify")
async def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return {"valid": True, "user_id": payload.get("user_id")}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
