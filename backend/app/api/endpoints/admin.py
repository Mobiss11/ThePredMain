"""
Admin Panel API Endpoints
Requires admin authentication (to be implemented)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case
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

    if status:
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

@router.get("/users", response_model=List[UserManagementItem])
async def get_all_users(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users for management
    """

    query = select(User).order_by(desc(User.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    users = result.scalars().all()

    return [UserManagementItem.from_orm(user) for user in users]


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

    if action == "approve":
        market.moderation_status = ModerationStatus.APPROVED
        market.status = MarketStatus.OPEN
        message = "Market approved and opened"
    else:
        market.moderation_status = ModerationStatus.REJECTED
        market.status = MarketStatus.CANCELLED
        message = "Market rejected"

    await db.commit()

    return {
        "market_id": market_id,
        "moderation_status": market.moderation_status,
        "status": market.status,
        "message": message
    }


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
    mission_type: str
    requirement: int
    reward_pred: int
    reward_ton: Optional[Decimal]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CreateMissionRequest(BaseModel):
    title: str
    description: str
    mission_type: str  # daily_bet, weekly_win, etc
    requirement: int
    reward_pred: int
    reward_ton: Optional[Decimal] = None
    is_active: bool = True


@router.get("/missions", response_model=List[MissionResponse])
async def get_all_missions(
    db: AsyncSession = Depends(get_db)
):
    """Get all missions"""
    query = select(Mission).order_by(desc(Mission.created_at))
    result = await db.execute(query)
    missions = result.scalars().all()

    return [MissionResponse.from_orm(mission) for mission in missions]


@router.post("/missions")
async def create_mission(
    mission_data: CreateMissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new mission"""
    new_mission = Mission(
        title=mission_data.title,
        description=mission_data.description,
        mission_type=mission_data.mission_type,
        requirement=mission_data.requirement,
        reward_pred=mission_data.reward_pred,
        reward_ton=mission_data.reward_ton,
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
    mission.mission_type = mission_data.mission_type
    mission.requirement = mission_data.requirement
    mission.reward_pred = mission_data.reward_pred
    mission.reward_ton = mission_data.reward_ton
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
    broadcast_data: BroadcastRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Broadcast a message to users via Telegram bot
    This endpoint stores the message and returns user list
    The actual sending should be done by the bot
    """
    from aiohttp import ClientSession

    # Get BOT_TOKEN from environment
    import os
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_TOKEN not configured")

    if broadcast_data.target == "all":
        # Get all users
        query = select(User.telegram_id)
        result = await db.execute(query)
        telegram_ids = [row[0] for row in result.all()]
    else:
        if not broadcast_data.telegram_id:
            raise HTTPException(status_code=400, detail="telegram_id required for specific user")
        telegram_ids = [broadcast_data.telegram_id]

    # Send messages via Telegram API
    sent_count = 0
    failed_count = 0

    async with ClientSession() as session:
        for telegram_id in telegram_ids:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": telegram_id,
                    "text": broadcast_data.message,
                    "parse_mode": broadcast_data.parse_mode
                }

                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        sent_count += 1
                    else:
                        failed_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Failed to send to {telegram_id}: {e}")

    return {
        "total_recipients": len(telegram_ids),
        "sent": sent_count,
        "failed": failed_count,
        "message": f"Broadcast sent to {sent_count} users"
    }


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
    db: AsyncSession = Depends(get_db)
):
    """Get leaderboard sorted by PRED balance"""
    query = select(User).order_by(desc(User.pred_balance)).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    leaderboard = []
    for rank, user in enumerate(users, start=1):
        win_rate = (user.total_wins / user.total_bets * 100) if user.total_bets > 0 else 0

        leaderboard.append({
            "rank": rank,
            "user_id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "pred_balance": user.pred_balance,
            "total_bets": user.total_bets,
            "total_wins": user.total_wins,
            "win_rate": round(win_rate, 2),
            "user_rank": user.rank
        })

    return leaderboard
