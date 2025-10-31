"""
Leaderboard endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, desc
from app.core.database import get_db
from app.models.user import User
from app.models.bet import Bet, BetStatus
from pydantic import BaseModel
from decimal import Decimal
from typing import List

router = APIRouter()


class LeaderboardEntry(BaseModel):
    """Leaderboard entry response model"""
    rank: int
    user_id: int
    username: str | None
    first_name: str | None
    rank_badge: str
    total_bets: int
    total_wins: int
    total_losses: int
    win_rate: float
    win_streak: int
    profit: Decimal

    class Config:
        from_attributes = True


@router.get("/", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    limit: int = 100,
    sort_by: str = "profit",  # profit, win_rate, win_streak, total_wins
    db: AsyncSession = Depends(get_db)
):
    """
    Get leaderboard rankings

    Sort options:
    - profit: Total profit (default)
    - win_rate: Win rate percentage
    - win_streak: Current win streak
    - total_wins: Total number of wins
    """

    # Calculate profit for each user
    # profit = sum(payouts from won bets) - sum(amounts from lost bets)
    profit_subquery = (
        select(
            Bet.user_id,
            func.sum(
                case(
                    (Bet.status == BetStatus.WON, Bet.payout - Bet.amount),
                    (Bet.status == BetStatus.LOST, -Bet.amount),
                    else_=Decimal("0.00")
                )
            ).label("profit")
        )
        .group_by(Bet.user_id)
        .subquery()
    )

    # Main query
    query = (
        select(
            User,
            func.coalesce(profit_subquery.c.profit, Decimal("0.00")).label("profit")
        )
        .outerjoin(profit_subquery, User.id == profit_subquery.c.user_id)
        .where(User.total_bets > 0)  # Only users with at least 1 bet
    )

    # Apply sorting
    if sort_by == "profit":
        query = query.order_by(desc("profit"))
    elif sort_by == "win_rate":
        query = query.order_by(
            desc(
                case(
                    (User.total_bets > 0, User.total_wins * 100.0 / User.total_bets),
                    else_=0
                )
            )
        )
    elif sort_by == "win_streak":
        query = query.order_by(desc(User.win_streak))
    elif sort_by == "total_wins":
        query = query.order_by(desc(User.total_wins))
    else:
        query = query.order_by(desc("profit"))

    # Add secondary sort by total_wins
    query = query.order_by(desc(User.total_wins))
    query = query.limit(limit)

    result = await db.execute(query)
    rows = result.all()

    # Build leaderboard entries
    leaderboard = []
    for rank, (user, profit) in enumerate(rows, start=1):
        win_rate = (user.total_wins / user.total_bets * 100) if user.total_bets > 0 else 0

        leaderboard.append(LeaderboardEntry(
            rank=rank,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            rank_badge=user.rank,
            total_bets=user.total_bets,
            total_wins=user.total_wins,
            total_losses=user.total_losses,
            win_rate=round(win_rate, 2),
            win_streak=user.win_streak,
            profit=profit
        ))

    return leaderboard


@router.get("/user/{user_id}")
async def get_user_rank(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user's current rank in leaderboard"""

    # Calculate profit for all users
    profit_subquery = (
        select(
            Bet.user_id,
            func.sum(
                case(
                    (Bet.status == BetStatus.WON, Bet.payout - Bet.amount),
                    (Bet.status == BetStatus.LOST, -Bet.amount),
                    else_=Decimal("0.00")
                )
            ).label("profit")
        )
        .group_by(Bet.user_id)
        .subquery()
    )

    # Get all users with their profits
    query = (
        select(
            User.id,
            func.coalesce(profit_subquery.c.profit, Decimal("0.00")).label("profit")
        )
        .outerjoin(profit_subquery, User.id == profit_subquery.c.user_id)
        .where(User.total_bets > 0)
        .order_by(desc("profit"), desc(User.total_wins))
    )

    result = await db.execute(query)
    all_users = result.all()

    # Find user's rank
    user_rank = None
    user_profit = Decimal("0.00")

    for rank, (uid, profit) in enumerate(all_users, start=1):
        if uid == user_id:
            user_rank = rank
            user_profit = profit
            break

    if user_rank is None:
        return {
            "user_id": user_id,
            "rank": None,
            "total_players": len(all_users),
            "profit": Decimal("0.00"),
            "message": "User not in leaderboard (no bets placed)"
        }

    return {
        "user_id": user_id,
        "rank": user_rank,
        "total_players": len(all_users),
        "profit": user_profit
    }
