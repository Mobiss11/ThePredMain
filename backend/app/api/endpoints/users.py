from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
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

    # Send Telegram notification to referrer
    try:
        await send_referral_notification(referrer.telegram_id, user.username or user.first_name or f"User #{user.telegram_id}")
    except Exception as e:
        import logging
        logging.error(f"Failed to send referral notification: {e}")

    return {
        "success": True,
        "bonus": settings.REFERRAL_BONUS_PRED
    }


@router.get("/{user_id}/referrals")
async def get_user_referrals(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user's referral statistics"""
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Count referrals (users who have this user as referrer)
    result = await db.execute(
        select(func.count(User.id)).where(User.referrer_id == user.id)
    )
    referral_count = result.scalar() or 0

    return {
        "referral_count": referral_count,
        "referral_bonus": 100  # PRED per referral
    }


async def send_referral_notification(telegram_id: int, referral_name: str):
    """Send Telegram notification when a referral is activated"""
    import os
    import aiohttp

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        return

    message = f"""
🎉 <b>Новый Реферал!</b>

<b>{referral_name}</b> зарегистрировался по вашей ссылке!

💰 Вы получили <b>+100 PRED</b>
    """.strip()

    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": telegram_id,
                "text": message,
                "parse_mode": "HTML"
            }
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    import logging
                    logging.error(f"Failed to send Telegram notification: {await response.text()}")
    except Exception as e:
        import logging
        logging.error(f"Error sending Telegram notification: {e}")
