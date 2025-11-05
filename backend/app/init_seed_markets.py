"""Initialize seed test markets on startup if database is empty"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.market import Market, MarketStatus
from app.models.user import User
from app.core.database import AsyncSessionLocal
from decimal import Decimal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


SEED_MARKETS = [
    {
        "title": "Will Bitcoin reach $100,000 by end of 2025?",
        "description": "Prediction market on whether Bitcoin (BTC) will hit $100,000 USD price point before December 31, 2025.",
        "category": "Crypto",
        "is_promoted": "premium"
    },
    {
        "title": "Will Ethereum ETF be approved in 2025?",
        "description": "Will the SEC approve a spot Ethereum ETF in the United States during 2025?",
        "category": "Crypto",
        "is_promoted": "basic"
    },
    {
        "title": "Will Manchester City win the Premier League?",
        "description": "Prediction for the 2024/25 Premier League champion",
        "category": "Sports",
        "is_promoted": "none"
    },
    {
        "title": "Will Trump win 2024 US Election?",
        "description": "Presidential election prediction for 2024",
        "category": "Politics",
        "is_promoted": "none"
    },
    {
        "title": "Will Tesla stock reach $300 in 2025?",
        "description": "Will Tesla (TSLA) stock price exceed $300 per share in 2025?",
        "category": "Finance",
        "is_promoted": "none"
    },
]


async def init_seed_markets():
    """Initialize seed markets if database has no markets"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if markets already exist
            result = await db.execute(select(Market))
            existing_markets = result.scalars().all()

            if len(existing_markets) > 0:
                logger.info(f"✓ Markets already exist ({len(existing_markets)} markets found)")
                return

            # Create seed admin user if needed
            result = await db.execute(select(User).where(User.telegram_id == 999999999))
            admin = result.scalar_one_or_none()

            if not admin:
                admin = User(
                    telegram_id=999999999,
                    username="admin",
                    first_name="Admin",
                    last_name="System",
                    pred_balance=Decimal("1000000.00"),
                    ton_balance=Decimal("100.00"),
                    rank="Admin"
                )
                db.add(admin)
                await db.flush()

            # Create seed markets
            logger.info(f"Creating {len(SEED_MARKETS)} seed markets...")

            for market_data in SEED_MARKETS:
                market = Market(
                    title=market_data["title"],
                    description=market_data["description"],
                    category=market_data["category"],
                    is_promoted=market_data["is_promoted"],
                    status=MarketStatus.OPEN,
                    created_by=admin.id,
                    resolve_date=datetime.utcnow() + timedelta(days=180),
                    yes_odds=Decimal("50.00"),
                    no_odds=Decimal("50.00"),
                    yes_pool_pred=Decimal("0.00"),
                    no_pool_pred=Decimal("0.00"),
                    yes_pool_ton=Decimal("0.00"),
                    no_pool_ton=Decimal("0.00"),
                    total_volume_pred=Decimal("0.00"),
                    total_volume_ton=Decimal("0.00")
                )
                db.add(market)

            await db.commit()
            logger.info(f"✓ Created {len(SEED_MARKETS)} seed markets")

        except Exception as e:
            logger.error(f"✗ Error initializing seed markets: {e}")
            await db.rollback()
            # Don't raise - this is not critical for startup
