from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.models.market import Market, MarketStatus
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

router = APIRouter()


class MarketResponse(BaseModel):
    id: int
    title: str
    description: str | None
    category: str | None
    yes_odds: Decimal
    no_odds: Decimal
    total_volume_pred: Decimal
    total_volume_ton: Decimal
    status: str
    bets_count: int
    views_count: int
    is_promoted: str
    created_at: datetime

    class Config:
        from_attributes = True


class MarketCreate(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    resolve_date: datetime | None = None


@router.get("/", response_model=list[MarketResponse])
async def get_markets(
    status: str = Query(default="open"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db)
):
    """Get list of markets"""
    query = select(Market)

    if status != "all":
        query = query.where(Market.status == MarketStatus(status))

    # Order by promoted first, then by volume
    query = query.order_by(
        desc(Market.is_promoted),
        desc(Market.total_volume_pred),
        desc(Market.created_at)
    ).limit(limit).offset(offset)

    result = await db.execute(query)
    markets = result.scalars().all()

    return markets


@router.get("/{market_id}", response_model=MarketResponse)
async def get_market(market_id: int, db: AsyncSession = Depends(get_db)):
    """Get market details"""
    result = await db.execute(select(Market).where(Market.id == market_id))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    # Increment views
    market.views_count += 1
    await db.commit()

    return market


@router.post("/", response_model=MarketResponse)
async def create_market(
    market_data: MarketCreate,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Create new market"""
    market = Market(
        title=market_data.title,
        description=market_data.description,
        category=market_data.category,
        resolve_date=market_data.resolve_date,
        created_by=user_id,
        yes_odds=Decimal("50.00"),
        no_odds=Decimal("50.00")
    )

    db.add(market)
    await db.commit()
    await db.refresh(market)

    return market


@router.get("/leaderboard/volume")
async def get_top_markets(
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get top markets by volume"""
    query = select(Market).where(
        Market.status == MarketStatus.OPEN
    ).order_by(
        desc(Market.total_volume_pred)
    ).limit(limit)

    result = await db.execute(query)
    markets = result.scalars().all()

    return markets
