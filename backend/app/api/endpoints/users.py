from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.database import get_db
from app.models.user import User
from pydantic import BaseModel
from decimal import Decimal

router = APIRouter()


class UserProfile(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    photo_url: str | None
    pred_balance: Decimal
    ton_balance: Decimal
    rank: str
    total_bets: int
    total_wins: int
    total_losses: int
    win_streak: int
    referral_code: str | None
    best_streak: int = 0
    global_rank: int | None = None

    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    pred_balance: Decimal
    ton_balance: Decimal


class ReferralActivation(BaseModel):
    referral_code: str


@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user profile"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/balance/{user_id}", response_model=BalanceResponse)
async def get_balance(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user balance"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return BalanceResponse(
        pred_balance=user.pred_balance,
        ton_balance=user.ton_balance
    )


@router.post("/referral/{user_id}")
async def activate_referral(
    user_id: int,
    referral_data: ReferralActivation,
    db: AsyncSession = Depends(get_db)
):
    """Activate referral code"""
    # Get current user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.referrer_id:
        raise HTTPException(status_code=400, detail="Referral already activated")

    # Find referrer
    result = await db.execute(
        select(User).where(User.referral_code == referral_data.referral_code)
    )
    referrer = result.scalar_one_or_none()

    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral code")

    if referrer.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot use own referral code")

    # Update user
    user.referrer_id = referrer.id

    # Give bonus to both users
    from app.core.config import settings
    user.pred_balance += Decimal(settings.REFERRAL_BONUS_PRED)
    referrer.pred_balance += Decimal(settings.REFERRAL_BONUS_PRED)

    await db.commit()

    return {
        "success": True,
        "bonus": settings.REFERRAL_BONUS_PRED
    }
