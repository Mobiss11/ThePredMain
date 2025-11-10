"""
Admin Panel API Endpoints
Requires admin authentication (to be implemented)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case, String, or_, and_
from app.core.database import get_db
from app.models.user import User
from app.models.market import Market, MarketStatus, MarketOutcome, ModerationStatus
from app.models.bet import Bet, BetStatus
from app.models.mission import Mission
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

router = APIRouter()


# ============ Pydantic Models ============

class CreateMarketRequest(BaseModel):
    """Request model for creating a new market"""
    title: str
    description: Optional[str] = None
    category: str
    resolve_date: Optional[datetime] = None
    is_promoted: str = "none"  # none, basic, premium
    promoted_until: Optional[datetime] = None


class ResolveMarketRequest(BaseModel):
    """Request model for resolving a market"""
    outcome: str  # YES, NO, or CANCELLED


class PlatformStats(BaseModel):
    """Platform statistics response"""
    total_users: int
    total_markets: int
    total_bets: int
    total_volume_pred: Decimal
    total_volume_ton: Decimal
    active_markets: int
    resolved_markets: int
    users_last_24h: int
    bets_last_24h: int
    volume_last_24h: Decimal


class UserManagementItem(BaseModel):
    """User management item"""
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    pred_balance: Decimal
    ton_balance: Decimal
    total_bets: int
    total_wins: int
    rank: str
    is_banned: bool = False
    ban_reason: Optional[str] = None
    photo_url: Optional[str] = None
    referral_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class MarketManagementItem(BaseModel):
    """Market management item"""
    id: int
    title: str
    category: str
    status: str
    yes_odds: Decimal
    no_odds: Decimal
    total_volume_pred: Decimal
    bets_count: int
    views_count: int
    is_promoted: str
    created_at: datetime
    resolve_date: Optional[datetime]

    class Config:
        from_attributes = True


# ============ Platform Stats ============

@router.get("/stats", response_model=PlatformStats)
async def get_platform_stats(db: AsyncSession = Depends(get_db)):
    """
    Get platform-wide statistics
    - Total users, markets, bets
    - Volume statistics
    - Recent activity (24h)
    """

    # Total counts
    total_users = await db.scalar(select(func.count(User.id)))
    total_markets = await db.scalar(select(func.count(Market.id)))
    total_bets = await db.scalar(select(func.count(Bet.id)))

    # Volume statistics
    total_volume_pred = await db.scalar(
        select(func.coalesce(func.sum(Market.total_volume_pred), Decimal("0.00")))
    ) or Decimal("0.00")

    total_volume_ton = await db.scalar(
        select(func.coalesce(func.sum(Market.total_volume_ton), Decimal("0.00")))
    ) or Decimal("0.00")

    # Market status counts
    active_markets = await db.scalar(
        select(func.count(Market.id)).where(Market.status == MarketStatus.OPEN)
    )

    resolved_markets = await db.scalar(
        select(func.count(Market.id)).where(Market.status == MarketStatus.RESOLVED)
    )

    # Recent activity (last 24 hours)
    from datetime import timedelta
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)

    users_last_24h = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= yesterday)
    )

    bets_last_24h = await db.scalar(
        select(func.count(Bet.id)).where(Bet.created_at >= yesterday)
    )

    volume_last_24h = await db.scalar(
        select(func.coalesce(func.sum(Bet.amount), Decimal("0.00")))
        .where(Bet.created_at >= yesterday)
    ) or Decimal("0.00")

    return PlatformStats(
        total_users=total_users or 0,
        total_markets=total_markets or 0,
        total_bets=total_bets or 0,
        total_volume_pred=total_volume_pred,
        total_volume_ton=total_volume_ton,
        active_markets=active_markets or 0,
        resolved_markets=resolved_markets or 0,
        users_last_24h=users_last_24h or 0,
        bets_last_24h=bets_last_24h or 0,
        volume_last_24h=volume_last_24h
    )


# ============ Market Management ============

@router.post("/markets")
async def create_market(
    market_data: CreateMarketRequest,
    admin_id: int = 1,  # TODO: Get from auth
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new market
    Only admins can create markets
    """

    # Create market
    new_market = Market(
        title=market_data.title,
        description=market_data.description,
        category=market_data.category,
        resolve_date=market_data.resolve_date,
        is_promoted=market_data.is_promoted,
        promoted_until=market_data.promoted_until,
        created_by=admin_id,
        status=MarketStatus.OPEN
    )

    db.add(new_market)
    await db.commit()
    await db.refresh(new_market)

    return {
        "id": new_market.id,
        "title": new_market.title,
        "status": new_market.status,
        "message": "Market created successfully"
    }


@router.get("/markets", response_model=List[MarketManagementItem])
async def get_all_markets(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all markets for management
    Can filter by status
    """

    query = select(Market).order_by(desc(Market.created_at))

    # Only filter by status if it's not "all"
    if status and status != "all":
        query = query.where(Market.status == status)

    query = query.limit(limit)

    result = await db.execute(query)
    markets = result.scalars().all()

    return [MarketManagementItem.from_orm(market) for market in markets]


@router.put("/markets/{market_id}/resolve")
async def resolve_market(
    market_id: int,
    resolve_data: ResolveMarketRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resolve a market and distribute payouts to winners

    Steps:
    1. Update market status and outcome
    2. Find all bets for this market
    3. Update bet statuses (WON/LOST)
    4. Calculate and update payouts for winners
    5. Update user balances
    6. Update user statistics (total_wins, total_losses, win_streak)
    """

    # Get market
    result = await db.execute(select(Market).where(Market.id == market_id))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    if market.status != MarketStatus.OPEN:
        raise HTTPException(status_code=400, detail="Market is not open")

    # Parse outcome
    outcome = resolve_data.outcome.upper()
    if outcome not in ["YES", "NO", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Invalid outcome. Must be YES, NO, or CANCELLED")

    # Update market status
    market.status = MarketStatus.RESOLVED
    market.outcome = MarketOutcome.YES if outcome == "YES" else (
        MarketOutcome.NO if outcome == "NO" else MarketOutcome.CANCELLED
    )
    market.resolved_at = datetime.utcnow()

    # Get all bets for this market
    bets_result = await db.execute(
        select(Bet).where(Bet.market_id == market_id, Bet.status == BetStatus.PENDING)
    )
    bets = bets_result.scalars().all()

    if outcome == "CANCELLED":
        # Refund all bets
        for bet in bets:
            bet.status = BetStatus.REFUNDED
            bet.payout = bet.amount

            # Return funds to user
            user_result = await db.execute(select(User).where(User.id == bet.user_id))
            user = user_result.scalar_one()

            if bet.currency == "PRED":
                user.pred_balance += bet.amount
            else:
                user.ton_balance += bet.amount

    else:
        # Calculate payouts for winners
        winning_position = outcome  # "YES" or "NO"

        # Get winning pool size
        if winning_position == "YES":
            winning_pool = market.yes_pool_pred if bets[0].currency == "PRED" else market.yes_pool_ton
            losing_pool = market.no_pool_pred if bets[0].currency == "PRED" else market.no_pool_ton
        else:
            winning_pool = market.no_pool_pred if bets[0].currency == "PRED" else market.no_pool_ton
            losing_pool = market.yes_pool_pred if bets[0].currency == "PRED" else market.yes_pool_ton

        for bet in bets:
            user_result = await db.execute(select(User).where(User.id == bet.user_id))
            user = user_result.scalar_one()

            if bet.position.upper() == winning_position:
                # Winner - calculate payout
                bet.status = BetStatus.WON

                # Payout = bet amount + (bet amount / winning pool) * losing pool
                if winning_pool > 0:
                    share_of_losing_pool = (bet.amount / winning_pool) * losing_pool
                    bet.payout = bet.amount + share_of_losing_pool
                else:
                    bet.payout = bet.amount  # Just return bet if no winning pool

                # Add payout to user balance
                if bet.currency == "PRED":
                    user.pred_balance += bet.payout
                else:
                    user.ton_balance += bet.payout

                # Update user stats
                user.total_wins += 1
                user.win_streak += 1

                # Update rank based on win streak
                if user.win_streak >= 50:
                    user.rank = "Grandmaster"
                elif user.win_streak >= 30:
                    user.rank = "Master"
                elif user.win_streak >= 20:
                    user.rank = "Diamond"
                elif user.win_streak >= 10:
                    user.rank = "Platinum"
                elif user.win_streak >= 5:
                    user.rank = "Gold"
                elif user.win_streak >= 3:
                    user.rank = "Silver"

            else:
                # Loser
                bet.status = BetStatus.LOST
                bet.payout = Decimal("0.00")

                # Update user stats
                user.total_losses += 1
                user.win_streak = 0  # Reset streak

                # Potentially downrank
                if user.total_losses > user.total_wins * 2:
                    user.rank = "Bronze"

    await db.commit()

    # Update mission progress for all users who had bets on this market
    try:
        from app.services.mission_service import MissionService
        user_ids = set(bet.user_id for bet in bets)
        for user_id in user_ids:
            try:
                await MissionService.check_and_update_all_missions(db, user_id)
            except Exception as e:
                # Log error but continue with other users
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to update missions for user {user_id} after market resolve: {e}")
    except Exception as e:
        # Log error but don't fail the resolve
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to update mission progress after market resolve: {e}")

    return {
        "market_id": market_id,
        "outcome": outcome,
        "bets_processed": len(bets),
        "message": f"Market resolved with outcome: {outcome}"
    }


@router.delete("/markets/{market_id}")
async def delete_market(
    market_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a market (only if no bets placed)
    """

    result = await db.execute(select(Market).where(Market.id == market_id))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    if market.bets_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete market with bets. Resolve or cancel it instead."
        )

    await db.delete(market)
    await db.commit()

    return {"message": "Market deleted successfully"}


@router.put("/markets/{market_id}/promote")
async def promote_market(
    market_id: int,
    promotion_level: str,  # none, basic, premium
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """
    Promote a market (feature it on homepage)
    """

    if promotion_level not in ["none", "basic", "premium"]:
        raise HTTPException(status_code=400, detail="Invalid promotion level")

    result = await db.execute(select(Market).where(Market.id == market_id))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    market.is_promoted = promotion_level

    if promotion_level != "none":
        from datetime import timedelta
        market.promoted_until = datetime.utcnow() + timedelta(hours=hours)
    else:
        market.promoted_until = None

    await db.commit()

    return {
        "market_id": market_id,
        "promotion_level": promotion_level,
        "promoted_until": market.promoted_until,
        "message": "Market promotion updated"
    }


# ============ User Management ============

@router.get("/users")
async def get_all_users(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    is_banned: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users for management with filters, sorting, and pagination

    Filters:
    - search: Search by username, first_name, telegram_id
    - is_banned: Filter by ban status
    - date_from, date_to: Filter by registration date range

    Sorting:
    - sort_by: pred_balance_asc, pred_balance_desc, ton_balance_asc, ton_balance_desc, created_at_desc (default)
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[GET /admin/users] Params: limit={limit}, offset={offset}, search={search}, is_banned={is_banned}, date_from={date_from}, date_to={date_to}, sort_by={sort_by}")

    # Base query
    query = select(User)
    count_query = select(func.count(User.id))

    # Apply search filter
    if search:
        search_filter = or_(
            User.username.ilike(f"%{search}%"),
            User.first_name.ilike(f"%{search}%"),
            User.telegram_id.cast(String).ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Apply banned filter
    if is_banned is not None:
        query = query.where(User.is_banned == is_banned)
        count_query = count_query.where(User.is_banned == is_banned)

    # Apply date range filter
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.where(User.created_at >= date_from_dt)
            count_query = count_query.where(User.created_at >= date_from_dt)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.where(User.created_at <= date_to_dt)
            count_query = count_query.where(User.created_at <= date_to_dt)
        except ValueError:
            pass

    # Apply sorting
    if sort_by == "pred_balance_asc":
        query = query.order_by(User.pred_balance.asc())
    elif sort_by == "pred_balance_desc":
        query = query.order_by(User.pred_balance.desc())
    elif sort_by == "ton_balance_asc":
        query = query.order_by(User.ton_balance.asc())
    elif sort_by == "ton_balance_desc":
        query = query.order_by(User.ton_balance.desc())
    else:
        # Default: newest first
        query = query.order_by(desc(User.created_at))

    # Get total count
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    # Get referral counts for all users
    referral_counts_dict = {}
    if users:
        user_ids = [user.id for user in users]
        referral_counts_query = select(
            User.referrer_id,
            func.count(User.id).label('count')
        ).where(
            User.referrer_id.in_(user_ids)
        ).group_by(User.referrer_id)

        referral_counts_result = await db.execute(referral_counts_query)
        referral_counts_dict = {row[0]: row[1] for row in referral_counts_result.all()}

    # Build response items
    user_items = []
    for user in users:
        user_dict = {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "pred_balance": user.pred_balance,
            "ton_balance": user.ton_balance,
            "total_bets": user.total_bets,
            "total_wins": user.total_wins,
            "rank": user.rank,
            "is_banned": user.is_banned,
            "ban_reason": user.ban_reason,
            "photo_url": user.photo_url,
            "referral_count": referral_counts_dict.get(user.id, 0),
            "created_at": user.created_at
        }
        user_items.append(user_dict)

    return {
        "users": user_items,
        "total": total_count,
        "limit": limit,
        "offset": offset
    }


@router.put("/users/{user_id}/balance")
async def update_user_balance(
    user_id: int,
    pred_balance: Optional[Decimal] = None,
    ton_balance: Optional[Decimal] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually update user balance (admin only)
    """

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if pred_balance is not None:
        user.pred_balance = pred_balance

    if ton_balance is not None:
        user.ton_balance = ton_balance

    await db.commit()

    return {
        "user_id": user_id,
        "pred_balance": user.pred_balance,
        "ton_balance": user.ton_balance,
        "message": "User balance updated"
    }


@router.put("/users/{user_id}/rank")
async def update_user_rank(
    user_id: int,
    rank: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually update user rank (admin only)
    """

    valid_ranks = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster"]

    if rank not in valid_ranks:
        raise HTTPException(status_code=400, detail=f"Invalid rank. Must be one of: {', '.join(valid_ranks)}")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.rank = rank
    await db.commit()

    return {
        "user_id": user_id,
        "rank": rank,
        "message": "User rank updated"
    }


@router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed user activity
    """

    # Get user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user's bets
    bets_result = await db.execute(
        select(Bet)
        .where(Bet.user_id == user_id)
        .order_by(desc(Bet.created_at))
        .limit(10)
    )
    recent_bets = bets_result.scalars().all()

    # Calculate profit
    profit_result = await db.execute(
        select(
            func.sum(
                case(
                    (Bet.status == BetStatus.WON, Bet.payout - Bet.amount),
                    (Bet.status == BetStatus.LOST, -Bet.amount),
                    else_=Decimal("0.00")
                )
            )
        ).where(Bet.user_id == user_id)
    )
    total_profit = profit_result.scalar() or Decimal("0.00")

    return {
        "user_id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "balances": {
            "pred": user.pred_balance,
            "ton": user.ton_balance
        },
        "stats": {
            "total_bets": user.total_bets,
            "total_wins": user.total_wins,
            "total_losses": user.total_losses,
            "win_rate": round((user.total_wins / user.total_bets * 100), 2) if user.total_bets > 0 else 0,
            "win_streak": user.win_streak,
            "total_profit": total_profit
        },
        "rank": user.rank,
        "recent_bets": [
            {
                "id": bet.id,
                "market_id": bet.market_id,
                "position": bet.position,
                "amount": bet.amount,
                "status": bet.status,
                "payout": bet.payout,
                "created_at": bet.created_at
            }
            for bet in recent_bets
        ]
    }


# ============ Market Moderation ============

@router.get("/markets/pending", response_model=List[MarketManagementItem])
async def get_pending_markets(
    db: AsyncSession = Depends(get_db)
):
    """Get all pending markets for moderation"""
    query = select(Market).where(
        Market.moderation_status == ModerationStatus.PENDING
    ).order_by(desc(Market.created_at))

    result = await db.execute(query)
    markets = result.scalars().all()

    return [MarketManagementItem.from_orm(market) for market in markets]


@router.get("/markets/approved", response_model=List[MarketManagementItem])
async def get_approved_markets(
    db: AsyncSession = Depends(get_db)
):
    """Get all approved markets"""
    query = select(Market).where(
        Market.moderation_status == ModerationStatus.APPROVED
    ).order_by(desc(Market.created_at))

    result = await db.execute(query)
    markets = result.scalars().all()

    return [MarketManagementItem.from_orm(market) for market in markets]


@router.get("/markets/cancelled", response_model=List[MarketManagementItem])
async def get_cancelled_markets(
    db: AsyncSession = Depends(get_db)
):
    """Get all cancelled markets"""
    query = select(Market).where(
        Market.status == MarketStatus.CANCELLED
    ).order_by(desc(Market.created_at))

    result = await db.execute(query)
    markets = result.scalars().all()

    return [MarketManagementItem.from_orm(market) for market in markets]


@router.put("/markets/{market_id}/moderate")
async def moderate_market(
    market_id: int,
    action: str,  # approve or reject
    db: AsyncSession = Depends(get_db)
):
    """Approve or reject a pending market"""
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    result = await db.execute(select(Market).where(Market.id == market_id))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    if market.moderation_status != ModerationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Market is not pending moderation")

    # Get market creator
    creator_result = await db.execute(select(User).where(User.id == market.created_by))
    creator = creator_result.scalar_one_or_none()

    if action == "approve":
        market.moderation_status = ModerationStatus.APPROVED
        market.status = MarketStatus.OPEN
        message = "Market approved and opened"

        # Send Telegram notification to creator
        if creator and creator.telegram_id:
            await send_telegram_notification(
                telegram_id=creator.telegram_id,
                message=f"✅ <b>Ваше событие одобрено!</b>\n\n"
                        f"<b>{market.title}</b>\n\n"
                        f"Событие опубликовано и доступно для ставок.\n"
                        f"Смотреть событие: /market_{market_id}"
            )
    else:
        market.moderation_status = ModerationStatus.REJECTED
        market.status = MarketStatus.CANCELLED
        message = "Market rejected"

        # Send rejection notification
        if creator and creator.telegram_id:
            await send_telegram_notification(
                telegram_id=creator.telegram_id,
                message=f"❌ <b>Ваше событие отклонено</b>\n\n"
                        f"<b>{market.title}</b>\n\n"
                        f"Событие не прошло модерацию. Пожалуйста, проверьте правила создания событий."
            )

    await db.commit()

    return {
        "market_id": market_id,
        "moderation_status": market.moderation_status,
        "status": market.status,
        "message": message
    }


async def send_telegram_notification(telegram_id: int, message: str):
    """Send notification to user via Telegram Bot API"""
    import os
    from aiohttp import ClientSession

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("BOT_TOKEN not configured, skipping notification")
        return

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": "HTML"
        }

        async with ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Failed to send Telegram notification: {error_text}")
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")


@router.put("/markets/{market_id}/close")
async def close_market(
    market_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Close a market (no more bets accepted)"""
    result = await db.execute(select(Market).where(Market.id == market_id))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    if market.status != MarketStatus.OPEN:
        raise HTTPException(status_code=400, detail="Market is not open")

    market.status = MarketStatus.CLOSED

    await db.commit()

    return {
        "market_id": market_id,
        "status": market.status,
        "message": "Market closed successfully"
    }


@router.put("/markets/{market_id}/cancel")
async def cancel_market(
    market_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a market and refund all bets"""
    result = await db.execute(select(Market).where(Market.id == market_id))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    if market.status == MarketStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Cannot cancel resolved market")

    # Update market status
    market.status = MarketStatus.CANCELLED
    market.outcome = MarketOutcome.CANCELLED

    # Refund all bets
    bets_result = await db.execute(
        select(Bet).where(Bet.market_id == market_id, Bet.status == BetStatus.PENDING)
    )
    bets = bets_result.scalars().all()

    refunded_count = 0
    for bet in bets:
        bet.status = BetStatus.REFUNDED
        bet.payout = bet.amount

        # Return funds to user
        user_result = await db.execute(select(User).where(User.id == bet.user_id))
        user = user_result.scalar_one()

        if bet.currency == "PRED":
            user.pred_balance += bet.amount
        else:
            user.ton_balance += bet.amount

        refunded_count += 1

    await db.commit()

    return {
        "market_id": market_id,
        "status": market.status,
        "bets_refunded": refunded_count,
        "message": "Market cancelled and all bets refunded"
    }


# ============ Missions Management ============

class MissionResponse(BaseModel):
    id: int
    title: str
    description: str
    icon: Optional[str] = None
    type: str  # daily, weekly, special, achievement
    requirements: dict  # {"bets_count": 3} or {"wins_count": 1}
    reward_amount: Decimal
    reward_currency: str  # PRED, TON
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CreateMissionRequest(BaseModel):
    title: str
    description: str
    icon: Optional[str] = "first_bet"
    type: str  # daily, weekly, special, achievement
    requirements: dict  # {"bets_count": 3} or {"wins_count": 1}
    reward_amount: Decimal
    reward_currency: str = "PRED"
    is_active: bool = True


@router.get("/missions", response_model=List[MissionResponse])
async def get_all_missions(
    db: AsyncSession = Depends(get_db)
):
    """Get all missions"""
    query = select(Mission).order_by(desc(Mission.created_at))
    result = await db.execute(query)
    missions = result.scalars().all()

    return [MissionResponse.model_validate(mission) for mission in missions]


@router.post("/missions")
async def create_mission(
    mission_data: CreateMissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new mission"""
    new_mission = Mission(
        title=mission_data.title,
        description=mission_data.description,
        icon=mission_data.icon,
        type=mission_data.type,
        requirements=mission_data.requirements,
        reward_amount=mission_data.reward_amount,
        reward_currency=mission_data.reward_currency,
        is_active=mission_data.is_active
    )

    db.add(new_mission)
    await db.commit()
    await db.refresh(new_mission)

    return {
        "id": new_mission.id,
        "title": new_mission.title,
        "message": "Mission created successfully"
    }


@router.put("/missions/{mission_id}")
async def update_mission(
    mission_id: int,
    mission_data: CreateMissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update a mission"""
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission.title = mission_data.title
    mission.description = mission_data.description
    mission.icon = mission_data.icon
    mission.type = mission_data.type
    mission.requirements = mission_data.requirements
    mission.reward_amount = mission_data.reward_amount
    mission.reward_currency = mission_data.reward_currency
    mission.is_active = mission_data.is_active

    await db.commit()

    return {
        "id": mission_id,
        "message": "Mission updated successfully"
    }


@router.delete("/missions/{mission_id}")
async def delete_mission(
    mission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a mission"""
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    await db.delete(mission)
    await db.commit()

    return {"message": "Mission deleted successfully"}


# ============ Broadcast Messages ============

class BroadcastRequest(BaseModel):
    message: str
    target: str = "all"  # "all" or specific telegram_id
    telegram_id: Optional[int] = None
    parse_mode: str = "HTML"  # HTML or Markdown


@router.post("/broadcast")
async def broadcast_message(
    message: str = Form(...),
    target: str = Form("all"),
    parse_mode: str = Form("HTML"),
    telegram_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Broadcast a message to users via Telegram bot queue

    Supports:
    - Text only (max 4096 chars)
    - Text with image (max 1000 chars)
    - HTML or Markdown formatting
    - All users or specific user

    Messages are added to queue and sent with rate limiting (30 msg/sec)
    """
    import logging
    logger = logging.getLogger(__name__)

    from app.services.telegram_queue_service import TelegramQueueService
    from app.models.telegram_notification import NotificationType

    # Validate message length
    max_length = 1000 if image else 4096
    if len(message) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Message too long! Max {max_length} characters {'with image' if image else ''}"
        )

    # Upload image to S3 if provided
    photo_url = None
    if image:
        try:
            import boto3
            import os
            from app.core.config import settings

            # Read image data
            image_data = await image.read()

            # Generate safe filename (only ASCII, no spaces or special chars)
            from datetime import datetime
            import uuid
            from pathlib import Path

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Get file extension safely
            ext = Path(image.filename).suffix.lower()  # .png, .jpg, etc
            # Generate unique ID to avoid collisions
            unique_id = str(uuid.uuid4())[:8]
            # Create safe filename: broadcast/20251110_075030_a1b2c3d4.png
            filename = f"broadcast/{timestamp}_{unique_id}{ext}"

            # Upload to S3
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY
            )

            s3_client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=filename,
                Body=image_data,
                ContentType=image.content_type,
                ACL='public-read'
            )

            photo_url = f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET}/{filename}"
            logger.info(f"[Broadcast] Uploaded image to S3: {photo_url}")

        except Exception as e:
            logger.error(f"[Broadcast] Failed to upload image: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload image")

    # Get recipients
    if target == "all":
        # Get all users
        query = select(User.telegram_id, User.id)
        result = await db.execute(query)
        recipients = [(row[0], row[1]) for row in result.all()]
    else:
        if not telegram_id:
            raise HTTPException(status_code=400, detail="telegram_id required for specific user")

        # Get specific user
        query = select(User.telegram_id, User.id).where(User.telegram_id == telegram_id)
        result = await db.execute(query)
        user_row = result.first()

        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")

        recipients = [(user_row[0], user_row[1])]

    # Add messages to queue
    queued_count = 0

    for telegram_id, user_id in recipients:
        try:
            # Prepare metadata
            metadata = {
                "broadcast": True,
                "photo_url": photo_url
            }

            # Add to queue
            await TelegramQueueService.add_notification(
                db=db,
                telegram_id=telegram_id,
                message_text=message,
                notification_type=NotificationType.BROADCAST,
                user_id=user_id,
                parse_mode=parse_mode,
                metadata=metadata
            )

            queued_count += 1

        except Exception as e:
            logger.error(f"[Broadcast] Failed to queue message for {telegram_id}: {e}")
            continue

    logger.info(f"[Broadcast] Queued {queued_count} messages out of {len(recipients)} recipients")

    return {
        "total_recipients": len(recipients),
        "queued": queued_count,
        "failed": len(recipients) - queued_count,
        "message": f"Broadcast queued for {queued_count} users",
        "photo_url": photo_url
    }


# ============ Scheduled Broadcasts ============

@router.post("/broadcast/schedule")
async def schedule_broadcast(
    message: str = Form(...),
    scheduled_at: str = Form(...),  # ISO 8601 datetime string in UTC
    target: str = Form("all"),
    parse_mode: str = Form("HTML"),
    telegram_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule a broadcast message for future delivery

    Args:
        message: Message text
        scheduled_at: UTC datetime in ISO 8601 format (e.g., "2025-11-10T15:30:00Z")
        target: "all" or "specific"
        parse_mode: "HTML" or "Markdown"
        telegram_id: Target user telegram_id if target="specific"
        image: Optional image file
    """
    import logging
    logger = logging.getLogger(__name__)

    from datetime import datetime, timezone
    from app.models.scheduled_broadcast import ScheduledBroadcast, BroadcastStatus

    # Parse scheduled datetime
    try:
        scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
        if scheduled_datetime.tzinfo is None:
            scheduled_datetime = scheduled_datetime.replace(tzinfo=timezone.utc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {e}")

    # Validate datetime is in the future
    if scheduled_datetime <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Scheduled time must be in the future")

    # Upload image to S3 if provided
    photo_url = None
    if image:
        try:
            import boto3
            import uuid
            from pathlib import Path
            from app.core.config import settings

            image_data = await image.read()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = Path(image.filename).suffix.lower()
            unique_id = str(uuid.uuid4())[:8]
            filename = f"broadcast/{timestamp}_{unique_id}{ext}"

            s3_client = boto3.client(
                's3',
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY
            )

            s3_client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=filename,
                Body=image_data,
                ContentType=image.content_type,
                ACL='public-read'
            )

            photo_url = f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET}/{filename}"
            logger.info(f"[Scheduled Broadcast] Uploaded image: {photo_url}")

        except Exception as e:
            logger.error(f"[Scheduled Broadcast] Failed to upload image: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload image")

    # Create scheduled broadcast
    scheduled_broadcast = ScheduledBroadcast(
        message_text=message,
        parse_mode=parse_mode,
        photo_url=photo_url,
        target=target,
        target_telegram_id=telegram_id if target == "specific" else None,
        scheduled_at=scheduled_datetime,
        status=BroadcastStatus.PENDING
    )

    db.add(scheduled_broadcast)
    await db.commit()
    await db.refresh(scheduled_broadcast)

    logger.info(f"[Scheduled Broadcast] Created broadcast ID {scheduled_broadcast.id} for {scheduled_datetime}")

    return {
        "id": scheduled_broadcast.id,
        "scheduled_at": scheduled_broadcast.scheduled_at.isoformat(),
        "message": "Broadcast scheduled successfully"
    }


@router.get("/broadcast/scheduled")
async def list_scheduled_broadcasts(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of scheduled broadcasts

    Args:
        status: Filter by status (PENDING, PROCESSING, COMPLETED, CANCELLED)
        limit: Max results
        offset: Pagination offset
    """
    from app.models.scheduled_broadcast import ScheduledBroadcast, BroadcastStatus

    query = select(ScheduledBroadcast).order_by(ScheduledBroadcast.scheduled_at.desc())

    if status:
        try:
            status_enum = BroadcastStatus(status)
            query = query.where(ScheduledBroadcast.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    broadcasts = result.scalars().all()

    return {
        "broadcasts": [
            {
                "id": b.id,
                "message_text": b.message_text[:100] + "..." if len(b.message_text) > 100 else b.message_text,
                "photo_url": b.photo_url,
                "target": b.target,
                "target_telegram_id": b.target_telegram_id,
                "scheduled_at": b.scheduled_at.isoformat(),
                "status": b.status.value,
                "total_recipients": b.total_recipients,
                "sent_count": b.sent_count,
                "created_at": b.created_at.isoformat(),
                "processed_at": b.processed_at.isoformat() if b.processed_at else None
            }
            for b in broadcasts
        ],
        "total": len(broadcasts),
        "limit": limit,
        "offset": offset
    }


@router.delete("/broadcast/scheduled/{broadcast_id}")
async def cancel_scheduled_broadcast(
    broadcast_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a scheduled broadcast"""
    from app.models.scheduled_broadcast import ScheduledBroadcast, BroadcastStatus
    from datetime import datetime, timezone

    result = await db.execute(
        select(ScheduledBroadcast).where(ScheduledBroadcast.id == broadcast_id)
    )
    broadcast = result.scalar_one_or_none()

    if not broadcast:
        raise HTTPException(status_code=404, detail="Scheduled broadcast not found")

    if broadcast.status != BroadcastStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel broadcast with status {broadcast.status.value}"
        )

    # Check if already processed
    if broadcast.scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Broadcast already processed or processing")

    broadcast.status = BroadcastStatus.CANCELLED
    await db.commit()

    return {"message": "Broadcast cancelled successfully"}


# ============ Leaderboard View ============

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    pred_balance: Decimal
    total_bets: int
    total_wins: int
    win_rate: float
    user_rank: str

    class Config:
        from_attributes = True


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = 100,
    period: str = "week",  # week or month
    db: AsyncSession = Depends(get_db)
):
    """
    Get leaderboard sorted by profit for the selected period
    Uses the same logic as the public leaderboard endpoint
    """
    from datetime import timedelta
    from app.models.bet import Bet, BetStatus

    # Calculate date range based on period
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
    else:  # month
        start_date = now - timedelta(days=30)

    # Calculate profit for each user (only for bets in period)
    profit_subquery = (
        select(
            Bet.user_id,
            func.sum(
                case(
                    (Bet.status == BetStatus.WON, Bet.payout - Bet.amount),
                    (Bet.status == BetStatus.LOST, -Bet.amount),
                    else_=Decimal("0.00")
                )
            ).label("profit"),
            func.count().label("bets_count")
        )
        .where(Bet.created_at >= start_date)
        .group_by(Bet.user_id)
        .subquery()
    )

    # Main query
    query = (
        select(
            User,
            func.coalesce(profit_subquery.c.profit, Decimal("0.00")).label("profit"),
            func.coalesce(profit_subquery.c.bets_count, 0).label("period_bets")
        )
        .outerjoin(profit_subquery, User.id == profit_subquery.c.user_id)
        .where(profit_subquery.c.bets_count > 0)  # Only users with bets in this period
        .order_by(desc("profit"))
        .order_by(desc(User.total_wins))
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    leaderboard = []
    for rank, (user, profit, period_bets) in enumerate(rows, start=1):
        win_rate = (user.total_wins / user.total_bets * 100) if user.total_bets > 0 else 0

        leaderboard.append({
            "rank": rank,
            "user_id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "photo_url": user.photo_url,
            "pred_balance": user.pred_balance,
            "total_bets": user.total_bets,
            "total_wins": user.total_wins,
            "win_rate": round(win_rate, 2),
            "user_rank": user.rank,
            "profit": profit,
            "period_bets": period_bets
        })

    return leaderboard


# ============ Leaderboard Rewards Management ============

from app.models.leaderboard_reward import LeaderboardReward, RewardPeriod


class LeaderboardRewardResponse(BaseModel):
    """Leaderboard reward response model"""
    id: int
    period: str
    rank_from: int
    rank_to: int
    reward_amount: int
    currency: str  # PRED or TON
    is_active: bool

    class Config:
        from_attributes = True


class CreateRewardRequest(BaseModel):
    """Request model for creating a reward"""
    period: str  # week or month
    rank_from: int
    rank_to: int
    reward_amount: int
    currency: str = "PRED"  # PRED or TON
    is_active: bool = True


class UpdateRewardRequest(BaseModel):
    """Request model for updating a reward"""
    period: Optional[str] = None
    rank_from: Optional[int] = None
    rank_to: Optional[int] = None
    reward_amount: Optional[int] = None
    currency: Optional[str] = None  # PRED or TON
    is_active: Optional[bool] = None


@router.get("/leaderboard/rewards", response_model=List[LeaderboardRewardResponse])
async def get_all_rewards(
    period: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all leaderboard rewards, optionally filtered by period"""
    from sqlalchemy import and_

    query = select(LeaderboardReward).order_by(
        LeaderboardReward.period,
        LeaderboardReward.rank_from
    )

    if period:
        reward_period = RewardPeriod.WEEK if period == "week" else RewardPeriod.MONTH
        query = query.where(LeaderboardReward.period == reward_period)

    result = await db.execute(query)
    rewards = result.scalars().all()

    return [LeaderboardRewardResponse.model_validate(reward) for reward in rewards]


@router.post("/leaderboard/rewards")
async def create_reward(
    reward_data: CreateRewardRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new leaderboard reward"""
    reward_period = RewardPeriod.WEEK if reward_data.period == "week" else RewardPeriod.MONTH

    new_reward = LeaderboardReward(
        period=reward_period,
        rank_from=reward_data.rank_from,
        rank_to=reward_data.rank_to,
        reward_amount=reward_data.reward_amount,
        currency=reward_data.currency,
        is_active=reward_data.is_active
    )

    db.add(new_reward)
    await db.commit()
    await db.refresh(new_reward)

    return {
        "id": new_reward.id,
        "period": new_reward.period.value,
        "rank_from": new_reward.rank_from,
        "rank_to": new_reward.rank_to,
        "reward_amount": new_reward.reward_amount,
        "currency": new_reward.currency,
        "message": "Reward created successfully"
    }


@router.put("/leaderboard/rewards/{reward_id}")
async def update_reward(
    reward_id: int,
    reward_data: UpdateRewardRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update a leaderboard reward"""
    result = await db.execute(
        select(LeaderboardReward).where(LeaderboardReward.id == reward_id)
    )
    reward = result.scalar_one_or_none()

    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    if reward_data.period is not None:
        reward.period = RewardPeriod.WEEK if reward_data.period == "week" else RewardPeriod.MONTH
    if reward_data.rank_from is not None:
        reward.rank_from = reward_data.rank_from
    if reward_data.rank_to is not None:
        reward.rank_to = reward_data.rank_to
    if reward_data.reward_amount is not None:
        reward.reward_amount = reward_data.reward_amount
    if reward_data.currency is not None:
        reward.currency = reward_data.currency
    if reward_data.is_active is not None:
        reward.is_active = reward_data.is_active

    await db.commit()

    return {
        "id": reward_id,
        "message": "Reward updated successfully"
    }


@router.delete("/leaderboard/rewards/{reward_id}")
async def delete_reward(
    reward_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a leaderboard reward"""
    result = await db.execute(
        select(LeaderboardReward).where(LeaderboardReward.id == reward_id)
    )
    reward = result.scalar_one_or_none()

    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    await db.delete(reward)
    await db.commit()

    return {"message": f"Reward {reward_id} deleted successfully"}


# ============ Mission Management ============

class CreateMissionRequest(BaseModel):
    """Request model for creating a mission"""
    title: str
    description: Optional[str] = None
    icon: str = "first_bet"  # Icon name or URL
    reward_amount: Decimal
    reward_currency: str = "PRED"
    type: str = "achievement"  # daily, weekly, special, achievement
    requirements: dict  # {"bets_count": 3} or {"wins_count": 1}
    is_active: bool = True


class UpdateMissionRequest(BaseModel):
    """Request model for updating a mission"""
    title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    reward_amount: Optional[Decimal] = None
    reward_currency: Optional[str] = None
    type: Optional[str] = None
    requirements: Optional[dict] = None
    is_active: Optional[bool] = None


@router.post("/missions", status_code=201)
async def create_mission(
    mission_data: CreateMissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new mission"""
    try:
        mission = Mission(
            title=mission_data.title,
            description=mission_data.description,
            icon=mission_data.icon,
            reward_amount=mission_data.reward_amount,
            reward_currency=mission_data.reward_currency,
            type=mission_data.type,
            requirements=mission_data.requirements,
            is_active=mission_data.is_active
        )

        db.add(mission)
        await db.commit()
        await db.refresh(mission)

        return {
            "id": mission.id,
            "title": mission.title,
            "description": mission.description,
            "icon": mission.icon,
            "reward_amount": mission.reward_amount,
            "reward_currency": mission.reward_currency,
            "type": mission.type,
            "requirements": mission.requirements,
            "is_active": mission.is_active,
            "created_at": mission.created_at
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create mission: {str(e)}")


@router.put("/missions/{mission_id}")
async def update_mission(
    mission_id: int,
    mission_data: UpdateMissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing mission"""
    # Get mission
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Update fields
    if mission_data.title is not None:
        mission.title = mission_data.title
    if mission_data.description is not None:
        mission.description = mission_data.description
    if mission_data.icon is not None:
        mission.icon = mission_data.icon
    if mission_data.reward_amount is not None:
        mission.reward_amount = mission_data.reward_amount
    if mission_data.reward_currency is not None:
        mission.reward_currency = mission_data.reward_currency
    if mission_data.type is not None:
        mission.type = mission_data.type
    if mission_data.requirements is not None:
        mission.requirements = mission_data.requirements
    if mission_data.is_active is not None:
        mission.is_active = mission_data.is_active

    await db.commit()
    await db.refresh(mission)

    return {
        "id": mission.id,
        "title": mission.title,
        "description": mission.description,
        "icon": mission.icon,
        "reward_amount": mission.reward_amount,
        "reward_currency": mission.reward_currency,
        "type": mission.type,
        "requirements": mission.requirements,
        "is_active": mission.is_active,
        "updated_at": mission.updated_at
    }


@router.delete("/missions/{mission_id}")
async def delete_mission(
    mission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a mission"""
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    await db.delete(mission)
    await db.commit()

    return {"message": f"Mission {mission_id} deleted successfully"}


@router.post("/missions/init-defaults")
async def init_default_missions_endpoint(db: AsyncSession = Depends(get_db)):
    """Initialize default missions (called from admin panel)"""
    from app.init_missions import init_default_missions

    try:
        # Check if missions already exist
        result = await db.execute(select(Mission))
        existing_missions = result.scalars().all()

        if len(existing_missions) > 0:
            return {
                "message": f"Missions already exist ({len(existing_missions)} missions found)",
                "created": 0,
                "existing": len(existing_missions)
            }

        # Call init function
        await init_default_missions()

        return {
            "message": "Default missions created successfully",
            "created": 7,
            "existing": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize missions: {str(e)}")


# ============ Test Markets Generation ============

@router.post("/markets/generate-test")
async def generate_test_markets(db: AsyncSession = Depends(get_db)):
    """Generate 5 test markets with photos for testing"""
    from datetime import datetime, timedelta

    test_markets = [
        {
            "title": "Bitcoin достигнет $100,000 до конца 2025?",
            "description": "Биткоин показывает сильный рост. Достигнет ли он отметки в $100,000 до 31 декабря 2025?",
            "category": "Crypto",
            "resolve_date": datetime.now() + timedelta(days=60),
            "is_promoted": "premium",
            "promoted_until": datetime.now() + timedelta(days=30),
            "photo_url": "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=800&h=600&fit=crop"
        },
        {
            "title": "TON Coin вырастет на 50% в ноябре?",
            "description": "TON показывает активный рост. Вырастет ли цена на 50% или больше до конца ноября 2025?",
            "category": "Crypto",
            "resolve_date": datetime.now() + timedelta(days=27),
            "is_promoted": "basic",
            "promoted_until": datetime.now() + timedelta(days=7),
            "photo_url": "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?w=800&h=600&fit=crop"
        },
        {
            "title": "Реал Мадрид победит в Лиге Чемпионов 2025?",
            "description": "Реал Мадрид - фаворит турнира. Выиграют ли они Лигу Чемпионов в сезоне 2024/2025?",
            "category": "Sports",
            "resolve_date": datetime.now() + timedelta(days=200),
            "is_promoted": "premium",
            "promoted_until": datetime.now() + timedelta(days=14),
            "photo_url": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=800&h=600&fit=crop"
        },
        {
            "title": "UFC 300: Макгрегор вернется в октагон?",
            "description": "Conor McGregor объявил о возвращении. Выступит ли он на UFC 300 в 2025 году?",
            "category": "Sports",
            "resolve_date": datetime.now() + timedelta(days=120),
            "is_promoted": "basic",
            "promoted_until": datetime.now() + timedelta(days=10),
            "photo_url": "https://images.unsplash.com/photo-1555597673-b21d5c935865?w=800&h=600&fit=crop"
        },
        {
            "title": "Apple выпустит AR очки в 2025?",
            "description": "Ходят слухи о Apple AR/VR очках нового поколения. Выпустит ли Apple их в 2025 году?",
            "category": "Tech",
            "resolve_date": datetime.now() + timedelta(days=365),
            "is_promoted": "none",
            "promoted_until": None,
            "photo_url": "https://images.unsplash.com/photo-1592478411213-6153e4ebc07d?w=800&h=600&fit=crop"
        }
    ]

    created_markets = []

    try:
        for market_data in test_markets:
            market = Market(
                title=market_data["title"],
                description=market_data["description"],
                category=market_data["category"],
                resolve_date=market_data["resolve_date"],
                is_promoted=market_data["is_promoted"],
                promoted_until=market_data["promoted_until"],
                photo_url=market_data["photo_url"],
                status=MarketStatus.OPEN,
                moderation_status=ModerationStatus.APPROVED,
                created_by=1  # Admin user
            )

            db.add(market)
            await db.flush()
            created_markets.append({
                "id": market.id,
                "title": market.title,
                "category": market.category
            })

        await db.commit()

        return {
            "message": f"Successfully generated {len(test_markets)} test markets",
            "created": len(test_markets),
            "markets": created_markets
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate test markets: {str(e)}")


# ============ Leaderboard Periods Management ============

from app.models.leaderboard_period import LeaderboardPeriod, PeriodStatus
from app.services.leaderboard_service import LeaderboardService


class LeaderboardPeriodResponse(BaseModel):
    """Leaderboard period response model"""
    id: int
    period_type: str
    start_date: datetime
    end_date: datetime
    status: str
    total_rewards_distributed: int
    participants_count: int
    winners_count: int
    closed_at: Optional[datetime]
    closed_by_admin_id: Optional[int]

    class Config:
        from_attributes = True


@router.post("/leaderboard/close-period")
async def close_leaderboard_period(
    period_type: str = Query(..., regex="^(week|month)$"),
    admin_id: int = 1,  # TODO: Get from auth
    db: AsyncSession = Depends(get_db)
):
    """
    Закрыть текущий период и рассчитать награды

    Можно закрыть досрочно, даже если срок не подошел.
    После закрытия начинается новый период.
    """
    try:
        result = await LeaderboardService.close_period_and_calculate_rewards(
            db=db,
            period_type=period_type,
            admin_id=admin_id
        )

        return result
    except Exception as e:
        logger.error(f"Error closing period: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard/periods", response_model=List[LeaderboardPeriodResponse])
async def get_closed_periods(
    period_type: Optional[str] = Query(None, regex="^(week|month)$"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список закрытых периодов

    Для отображения истории в админке
    """
    periods = await LeaderboardService.get_closed_periods(
        db=db,
        period_type=period_type,
        limit=limit
    )

    return [LeaderboardPeriodResponse.model_validate(p) for p in periods]


@router.get("/leaderboard/current-stats")
async def get_current_period_stats(
    period_type: str = Query(..., regex="^(week|month)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить статистику текущего (незакрытого) периода

    Показывает сколько участников, потенциальные награды и т.д.
    """
    stats = await LeaderboardService.get_current_period_stats(
        db=db,
        period_type=period_type
    )

    return stats


@router.get("/notifications/queue-stats")
async def get_notifications_queue_stats(db: AsyncSession = Depends(get_db)):
    """
    Статистика очереди уведомлений

    Для мониторинга воркера отправки
    """
    from app.services.telegram_queue_service import TelegramQueueService

    stats = await TelegramQueueService.get_queue_stats(db=db)
    return stats


# ============ MISSIONS MANAGEMENT ============

class CreateMissionRequest(BaseModel):
    """Request model for creating a mission"""
    title: str
    description: Optional[str] = None
    icon: Optional[str] = "🎯"
    custom_icon_url: Optional[str] = None
    reward_amount: Decimal
    reward_currency: str = "PRED"
    type: str  # daily, weekly, achievement, subscription
    requirements: dict
    channel_id: Optional[str] = None
    channel_username: Optional[str] = None
    channel_url: Optional[str] = None
    is_active: bool = True


class UpdateMissionRequest(BaseModel):
    """Request model for updating a mission"""
    title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    custom_icon_url: Optional[str] = None
    reward_amount: Optional[Decimal] = None
    reward_currency: Optional[str] = None
    requirements: Optional[dict] = None
    channel_id: Optional[str] = None
    channel_username: Optional[str] = None
    channel_url: Optional[str] = None
    is_active: Optional[bool] = None


class MissionAdminResponse(BaseModel):
    """Mission response for admin"""
    id: int
    title: str
    description: Optional[str]
    icon: Optional[str]
    custom_icon_url: Optional[str]
    reward_amount: Decimal
    reward_currency: str
    type: str
    requirements: dict
    channel_id: Optional[str]
    channel_username: Optional[str]
    channel_url: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/missions", response_model=List[MissionAdminResponse])
async def get_all_missions(
    type_filter: Optional[str] = Query(None, description="Filter by type: daily, weekly, achievement, subscription"),
    db: AsyncSession = Depends(get_db)
):
    """Get all missions for admin panel"""
    query = select(Mission).order_by(Mission.type, Mission.id)

    if type_filter:
        from app.models.mission import Mission as MissionModel
        query = query.where(MissionModel.type == type_filter)

    result = await db.execute(query)
    missions = result.scalars().all()

    return missions


@router.post("/missions", response_model=MissionAdminResponse)
async def create_mission(
    mission_data: CreateMissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new mission"""
    from app.models.mission import Mission as MissionModel

    mission = MissionModel(
        title=mission_data.title,
        description=mission_data.description,
        icon=mission_data.icon,
        custom_icon_url=mission_data.custom_icon_url,
        reward_amount=mission_data.reward_amount,
        reward_currency=mission_data.reward_currency,
        type=mission_data.type,
        requirements=mission_data.requirements,
        channel_id=mission_data.channel_id,
        channel_username=mission_data.channel_username,
        channel_url=mission_data.channel_url,
        is_active=mission_data.is_active
    )

    db.add(mission)
    await db.commit()
    await db.refresh(mission)

    return mission


@router.put("/missions/{mission_id}", response_model=MissionAdminResponse)
async def update_mission(
    mission_id: int,
    mission_data: UpdateMissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing mission"""
    from app.models.mission import Mission as MissionModel

    result = await db.execute(select(MissionModel).where(MissionModel.id == mission_id))
    mission = result.scalar_one_or_none()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Update fields
    if mission_data.title is not None:
        mission.title = mission_data.title
    if mission_data.description is not None:
        mission.description = mission_data.description
    if mission_data.icon is not None:
        mission.icon = mission_data.icon
    if mission_data.custom_icon_url is not None:
        mission.custom_icon_url = mission_data.custom_icon_url
    if mission_data.reward_amount is not None:
        mission.reward_amount = mission_data.reward_amount
    if mission_data.reward_currency is not None:
        mission.reward_currency = mission_data.reward_currency
    if mission_data.requirements is not None:
        mission.requirements = mission_data.requirements
    if mission_data.channel_id is not None:
        mission.channel_id = mission_data.channel_id
    if mission_data.channel_username is not None:
        mission.channel_username = mission_data.channel_username
    if mission_data.channel_url is not None:
        mission.channel_url = mission_data.channel_url
    if mission_data.is_active is not None:
        mission.is_active = mission_data.is_active

    await db.commit()
    await db.refresh(mission)

    return mission


@router.delete("/missions/{mission_id}")
async def delete_mission(
    mission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a mission"""
    from app.models.mission import Mission as MissionModel

    result = await db.execute(select(MissionModel).where(MissionModel.id == mission_id))
    mission = result.scalar_one_or_none()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    await db.delete(mission)
    await db.commit()

    return {"success": True, "message": "Mission deleted"}


@router.get("/missions/stats")
async def get_missions_stats(db: AsyncSession = Depends(get_db)):
    """Get missions statistics"""
    from app.models.mission import Mission as MissionModel, UserMission

    # Total missions
    total_result = await db.execute(select(func.count(MissionModel.id)))
    total_missions = total_result.scalar()

    # Active missions
    active_result = await db.execute(
        select(func.count(MissionModel.id)).where(MissionModel.is_active == True)
    )
    active_missions = active_result.scalar()

    # Missions by type
    type_result = await db.execute(
        select(MissionModel.type, func.count(MissionModel.id))
        .group_by(MissionModel.type)
    )
    missions_by_type = {row[0]: row[1] for row in type_result.all()}

    # Total completions
    completions_result = await db.execute(
        select(func.count(UserMission.mission_id)).where(UserMission.completed == True)
    )
    total_completions = completions_result.scalar()

    # Total claims
    claims_result = await db.execute(
        select(func.count(UserMission.mission_id)).where(UserMission.claimed == True)
    )
    total_claims = claims_result.scalar()

    return {
        "total_missions": total_missions,
        "active_missions": active_missions,
        "missions_by_type": missions_by_type,
        "total_completions": total_completions,
        "total_claims": total_claims
    }


# ============ User Deletion ============

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user with CASCADE deletion of all related records

    Steps:
    1. Delete all user's bets
    2. Delete all user's transactions
    3. Delete all user's missions
    4. Delete all user's support tickets
    5. Delete all user's telegram notifications
    6. Clear referrer_id for users who were referred by this user
    7. Delete the user
    """
    import logging
    logger = logging.getLogger(__name__)

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Import necessary models
        from app.models.bet import Bet
        from app.models.transaction import Transaction
        from app.models.mission import UserMission
        from app.models.support import SupportTicket
        from app.models.telegram_notification import TelegramNotification
        from sqlalchemy import delete, update

        # 1. Delete all user's bets
        bets_result = await db.execute(delete(Bet).where(Bet.user_id == user_id))
        deleted_bets = bets_result.rowcount
        logger.info(f"Deleted {deleted_bets} bets for user {user_id}")

        # 2. Delete all user's transactions
        transactions_result = await db.execute(delete(Transaction).where(Transaction.user_id == user_id))
        deleted_transactions = transactions_result.rowcount
        logger.info(f"Deleted {deleted_transactions} transactions for user {user_id}")

        # 3. Delete all user's missions
        missions_result = await db.execute(delete(UserMission).where(UserMission.user_id == user_id))
        deleted_missions = missions_result.rowcount
        logger.info(f"Deleted {deleted_missions} user missions for user {user_id}")

        # 4. Delete all user's support tickets
        tickets_result = await db.execute(delete(SupportTicket).where(SupportTicket.user_id == user_id))
        deleted_tickets = tickets_result.rowcount
        logger.info(f"Deleted {deleted_tickets} support tickets for user {user_id}")

        # 5. Delete all user's telegram notifications
        notifications_result = await db.execute(delete(TelegramNotification).where(TelegramNotification.user_id == user_id))
        deleted_notifications = notifications_result.rowcount
        logger.info(f"Deleted {deleted_notifications} telegram notifications for user {user_id}")

        # 6. Clear referrer_id for users who were referred by this user
        referrals_result = await db.execute(
            update(User)
            .where(User.referrer_id == user_id)
            .values(referrer_id=None)
        )
        cleared_referrals = referrals_result.rowcount
        logger.info(f"Cleared referrer_id for {cleared_referrals} users")

        # 7. Delete the user
        await db.delete(user)
        await db.commit()

        logger.info(f"Successfully deleted user {user_id} (telegram_id: {user.telegram_id})")

        return {
            "success": True,
            "message": f"User {user_id} deleted successfully",
            "deleted_records": {
                "bets": deleted_bets,
                "transactions": deleted_transactions,
                "missions": deleted_missions,
                "support_tickets": deleted_tickets,
                "telegram_notifications": deleted_notifications,
                "cleared_referrals": cleared_referrals
            }
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


@router.put("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    reason: str = Query(..., description="Ban reason"),
    db: AsyncSession = Depends(get_db)
):
    """Ban a user"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Get user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Ban user
        user.is_banned = True
        user.ban_reason = reason
        user.banned_at = datetime.utcnow()

        await db.commit()

        logger.info(f"User {user_id} banned. Reason: {reason}")

        return {
            "success": True,
            "message": f"User {user_id} has been banned",
            "user_id": user_id,
            "is_banned": True,
            "ban_reason": reason
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error banning user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ban user: {str(e)}")


@router.put("/users/{user_id}/unban")
async def unban_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Unban a user"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Get user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Unban user
        user.is_banned = False
        user.ban_reason = None
        user.banned_at = None

        await db.commit()

        logger.info(f"User {user_id} unbanned")

        return {
            "success": True,
            "message": f"User {user_id} has been unbanned",
            "user_id": user_id,
            "is_banned": False
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error unbanning user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unban user: {str(e)}")


@router.post("/markets/create")
async def create_admin_event(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    resolve_date: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new admin event with optional photo upload"""
    import logging
    logger = logging.getLogger(__name__)

    photo_url = None

    # Upload photo to S3 if provided
    if photo:
        try:
            from app.core.s3 import s3_client

            # Read file content
            content = await photo.read()

            # Upload to S3
            photo_url = await s3_client.upload_file(
                file_content=content,
                filename=photo.filename,
                content_type=photo.content_type or "image/jpeg"
            )
            logger.info(f"Photo uploaded to S3: {photo_url}")
        except Exception as e:
            logger.error(f"Failed to upload photo: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")

    # Parse resolve date
    try:
        resolve_dt = datetime.fromisoformat(resolve_date.replace('Z', '+00:00'))
    except Exception as e:
        logger.error(f"Invalid date format: {resolve_date}, error: {e}")
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Create market with APPROVED status and no creator (admin event)
    market = Market(
        title=title,
        description=description,
        category=category,
        photo_url=photo_url,
        resolve_date=resolve_dt,
        created_by=None,  # Admin event - no creator
        moderation_status=ModerationStatus.APPROVED,  # Auto-approved
        yes_odds=Decimal("50.00"),
        no_odds=Decimal("50.00")
    )

    db.add(market)
    await db.commit()
    await db.refresh(market)

    logger.info(f"Admin event created: {market.id} - {market.title}")

    return {
        "success": True,
        "market_id": market.id,
        "title": market.title,
        "moderation_status": market.moderation_status,
        "photo_url": photo_url
    }
