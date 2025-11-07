from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.models.market import Market, MarketStatus, ModerationStatus
from app.core.s3 import s3_client
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional

router = APIRouter()


class MarketResponse(BaseModel):
    id: int
    title: str
    description: str | None
    category: str | None
    photo_url: str | None
    yes_odds: Decimal
    no_odds: Decimal
    total_volume_pred: Decimal
    total_volume_ton: Decimal
    status: str
    moderation_status: str
    bets_count: int
    views_count: int
    is_promoted: str
    resolve_date: datetime | None
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
    """Get list of markets (only approved)"""
    query = select(Market).where(Market.moderation_status == ModerationStatus.APPROVED)

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


@router.post("/create-event")
async def create_user_event(
    user_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    resolve_date: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new user event with optional photo upload"""
    photo_url = None

    # Upload photo to S3 if provided
    if photo:
        try:
            # Read file content
            content = await photo.read()

            # Upload to S3
            photo_url = await s3_client.upload_file(
                file_content=content,
                filename=photo.filename,
                content_type=photo.content_type or "image/jpeg"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")

    # Parse resolve date
    try:
        resolve_dt = datetime.fromisoformat(resolve_date.replace('Z', '+00:00'))
    except:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Create market with pending moderation status
    market = Market(
        title=title,
        description=description,
        category=category,
        photo_url=photo_url,
        resolve_date=resolve_dt,
        created_by=user_id,
        moderation_status=ModerationStatus.PENDING,
        yes_odds=Decimal("50.00"),
        no_odds=Decimal("50.00")
    )

    db.add(market)
    await db.commit()
    await db.refresh(market)

    return {
        "success": True,
        "market_id": market.id,
        "moderation_status": market.moderation_status
    }


@router.post("/", response_model=MarketResponse)
async def create_market(
    market_data: MarketCreate,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Create new market (admin)"""
    market = Market(
        title=market_data.title,
        description=market_data.description,
        category=market_data.category,
        resolve_date=market_data.resolve_date,
        created_by=user_id,
        moderation_status=ModerationStatus.APPROVED,
        yes_odds=Decimal("50.00"),
        no_odds=Decimal("50.00")
    )

    db.add(market)
    await db.commit()
    await db.refresh(market)

    return market


@router.get("/my-events/{user_id}", response_model=list[MarketResponse])
async def get_user_events(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's created events"""
    query = select(Market).where(
        Market.created_by == user_id
    ).order_by(desc(Market.created_at))

    result = await db.execute(query)
    markets = result.scalars().all()

    return markets


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


@router.get("/user/{user_id}", response_model=list[MarketResponse])
async def get_user_markets(
    user_id: int,
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db)
):
    """Get markets created by a specific user"""
    query = select(Market).where(
        Market.created_by == user_id
    )

    # Filter by status if provided
    if status:
        if status == "open":
            query = query.where(Market.status == MarketStatus.OPEN)
        elif status == "resolved":
            query = query.where(Market.status == MarketStatus.RESOLVED)
        elif status == "cancelled":
            query = query.where(Market.status == MarketStatus.CANCELLED)

    # Order by creation date (newest first)
    query = query.order_by(desc(Market.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    markets = result.scalars().all()

    return markets


class PromoteMarketRequest(BaseModel):
    market_id: int
    promotion_type: str  # basic, top_category, pinned, premium
    currency: str  # pred, ton


@router.post("/promote")
async def promote_market(
    request: PromoteMarketRequest,
    db: AsyncSession = Depends(get_db)
):
    """Purchase promotion for a market"""
    from app.models.user import User
    from app.models.transaction import Transaction, TransactionType
    from datetime import timedelta

    # Define promotion prices
    promotion_prices = {
        'basic': {'pred': 500, 'ton': 0.5, 'duration_days': 7, 'type': 'basic'},
        'top_category': {'pred': 1000, 'ton': 1, 'duration_days': 3, 'type': 'basic'},
        'pinned': {'pred': 2000, 'ton': 2, 'duration_days': 1, 'type': 'basic'},
        'premium': {'pred': 5000, 'ton': 5, 'duration_days': 7, 'type': 'premium'}
    }

    # Validate promotion type
    if request.promotion_type not in promotion_prices:
        raise HTTPException(status_code=400, detail="Invalid promotion type")

    if request.currency not in ['pred', 'ton']:
        raise HTTPException(status_code=400, detail="Invalid currency")

    # Get market
    market_query = select(Market).where(Market.id == request.market_id)
    market_result = await db.execute(market_query)
    market = market_result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    # Check if market is open
    if market.status != MarketStatus.OPEN:
        raise HTTPException(status_code=400, detail="Can only promote open markets")

    # Get user (market creator)
    user_query = select(User).where(User.id == market.created_by)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check user rank (must be Gold+)
    gold_plus_ranks = ['Gold', 'Diamond', 'Legend']
    if user.rank not in gold_plus_ranks:
        raise HTTPException(status_code=403, detail="Promotion is only available for Gold+ users")

    # Get price
    price = promotion_prices[request.promotion_type][request.currency]

    # Check balance
    if request.currency == 'pred':
        if user.pred_balance < Decimal(str(price)):
            raise HTTPException(status_code=400, detail="Insufficient PRED balance")

        # Deduct from balance
        old_balance = user.pred_balance
        user.pred_balance -= Decimal(str(price))

        # Create transaction
        transaction = Transaction(
            user_id=user.id,
            type=TransactionType.PRED_SPENT,
            amount_pred=-Decimal(str(price)),
            amount_ton=Decimal('0'),
            balance_before_pred=old_balance,
            balance_after_pred=user.pred_balance,
            balance_before_ton=user.ton_balance,
            balance_after_ton=user.ton_balance,
            description=f"Market promotion: {market.title} ({request.promotion_type})"
        )
    else:  # ton
        if user.ton_balance < Decimal(str(price)):
            raise HTTPException(status_code=400, detail="Insufficient TON balance")

        # Deduct from balance
        old_balance = user.ton_balance
        user.ton_balance -= Decimal(str(price))

        # Create transaction
        transaction = Transaction(
            user_id=user.id,
            type=TransactionType.TON_SPENT,
            amount_pred=Decimal('0'),
            amount_ton=-Decimal(str(price)),
            balance_before_pred=user.pred_balance,
            balance_after_pred=user.pred_balance,
            balance_before_ton=old_balance,
            balance_after_ton=user.ton_balance,
            description=f"Market promotion: {market.title} ({request.promotion_type})"
        )

    db.add(transaction)

    # Update market promotion
    promo_type = promotion_prices[request.promotion_type]['type']
    market.is_promoted = promo_type
    market.promoted_until = datetime.utcnow() + timedelta(
        days=promotion_prices[request.promotion_type]['duration_days']
    )

    await db.commit()

    return {
        "success": True,
        "message": f"Market promoted successfully with {request.promotion_type} plan",
        "promotion_type": promo_type,
        "expires_at": market.promoted_until.isoformat()
    }
