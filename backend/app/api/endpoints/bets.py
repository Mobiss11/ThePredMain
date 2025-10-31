from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.bet import Bet, BetPosition, BetCurrency, BetStatus
from app.models.market import Market, MarketStatus
from app.models.user import User
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

router = APIRouter()


class BetCreate(BaseModel):
    market_id: int
    position: str  # yes/no
    amount: Decimal
    currency: str  # PRED/TON


class BetResponse(BaseModel):
    id: int
    market_id: int
    position: str
    amount: Decimal
    currency: str
    odds: Decimal
    potential_win: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


def calculate_odds(yes_pool: Decimal, no_pool: Decimal, position: str, amount: Decimal) -> Decimal:
    """Calculate odds based on pool sizes"""
    total_pool = yes_pool + no_pool + amount

    if position == "yes":
        new_yes_pool = yes_pool + amount
        if new_yes_pool == 0:
            return Decimal("100.00")
        yes_percentage = (new_yes_pool / total_pool) * 100
        return yes_percentage

    else:  # no
        new_no_pool = no_pool + amount
        if new_no_pool == 0:
            return Decimal("100.00")
        no_percentage = (new_no_pool / total_pool) * 100
        return no_percentage


@router.post("/", response_model=BetResponse)
async def place_bet(
    bet_data: BetCreate,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Place a bet"""
    # Get market
    result = await db.execute(select(Market).where(Market.id == bet_data.market_id))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    if market.status != MarketStatus.OPEN:
        raise HTTPException(status_code=400, detail="Market is not open")

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check balance
    currency = BetCurrency(bet_data.currency)
    if currency == BetCurrency.PRED and user.pred_balance < bet_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient PRED balance")
    elif currency == BetCurrency.TON and user.ton_balance < bet_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient TON balance")

    # Calculate odds
    position = BetPosition(bet_data.position)
    if currency == BetCurrency.PRED:
        odds = calculate_odds(
            market.yes_pool_pred,
            market.no_pool_pred,
            bet_data.position,
            bet_data.amount
        )
    else:
        odds = calculate_odds(
            market.yes_pool_ton,
            market.no_pool_ton,
            bet_data.position,
            bet_data.amount
        )

    # Calculate potential win
    from app.core.config import settings
    commission = settings.COMMISSION_PRED if currency == BetCurrency.PRED else settings.COMMISSION_TON
    opposite_pool = market.no_pool_pred if position == BetPosition.YES else market.yes_pool_pred

    if currency == BetCurrency.TON:
        opposite_pool = market.no_pool_ton if position == BetPosition.YES else market.yes_pool_ton

    if opposite_pool > 0:
        potential_win = bet_data.amount + (bet_data.amount * opposite_pool / (
            market.yes_pool_pred if position == BetPosition.YES else market.no_pool_pred
        ))
    else:
        potential_win = bet_data.amount * 2

    potential_win = potential_win * (1 - Decimal(str(commission)))

    # Deduct balance
    if currency == BetCurrency.PRED:
        user.pred_balance -= bet_data.amount
    else:
        user.ton_balance -= bet_data.amount

    # Update market pools
    if currency == BetCurrency.PRED:
        if position == BetPosition.YES:
            market.yes_pool_pred += bet_data.amount
        else:
            market.no_pool_pred += bet_data.amount
        market.total_volume_pred += bet_data.amount
    else:
        if position == BetPosition.YES:
            market.yes_pool_ton += bet_data.amount
        else:
            market.no_pool_ton += bet_data.amount
        market.total_volume_ton += bet_data.amount

    # Update market odds
    total = market.yes_pool_pred + market.no_pool_pred
    if total > 0:
        market.yes_odds = (market.yes_pool_pred / total) * 100
        market.no_odds = (market.no_pool_pred / total) * 100

    market.bets_count += 1

    # Create bet
    bet = Bet(
        user_id=user_id,
        market_id=bet_data.market_id,
        position=position,
        amount=bet_data.amount,
        currency=currency,
        odds=odds,
        potential_win=potential_win,
        status=BetStatus.PENDING
    )

    # Update user stats
    user.total_bets += 1

    db.add(bet)
    await db.commit()
    await db.refresh(bet)

    return bet


@router.get("/history/{user_id}", response_model=list[BetResponse])
async def get_bet_history(
    user_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get user bet history"""
    query = select(Bet).where(
        Bet.user_id == user_id
    ).order_by(desc(Bet.created_at)).limit(limit)

    result = await db.execute(query)
    bets = result.scalars().all()

    return bets


@router.get("/active/{user_id}", response_model=list[BetResponse])
async def get_active_bets(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user active bets"""
    query = select(Bet).where(
        Bet.user_id == user_id,
        Bet.status == BetStatus.PENDING
    ).order_by(desc(Bet.created_at))

    result = await db.execute(query)
    bets = result.scalars().all()

    return bets
