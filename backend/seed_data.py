"""
Seed data script for ThePred database
Adds test markets, users, and missions
"""
import asyncio
import sys
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add app directory to path
sys.path.insert(0, '.')

from app.core.config import settings
from app.models.user import User
from app.models.market import Market, MarketStatus
from app.models.mission import Mission


async def seed_database():
    """Seed the database with test data"""

    # Create async engine
    engine = create_async_engine(settings.database_url, echo=True)

    # Create session maker
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("\n🌱 Starting database seeding...\n")

        # Create admin user
        print("Creating admin user...")
        admin = User(
            telegram_id=999999999,
            username="admin",
            first_name="Admin",
            last_name="User",
            pred_balance=Decimal("1000000.00"),
            ton_balance=Decimal("100.00"),
            rank="Admin"
        )
        session.add(admin)
        await session.flush()

        # Create test user
        print("Creating test user...")
        test_user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            pred_balance=Decimal("1000.00"),
            ton_balance=Decimal("0.00"),
            rank="Bronze"
        )
        session.add(test_user)
        await session.flush()

        print(f"✅ Created {2} users\n")

        # Create test markets
        print("Creating test markets...")

        markets_data = [
            {
                "title": "Will Bitcoin reach $100,000 by end of 2025?",
                "description": "Prediction market on whether Bitcoin (BTC) will hit $100,000 USD price point before December 31, 2025.",
                "category": "Crypto",
                "yes_odds": Decimal("72.00"),
                "no_odds": Decimal("28.00"),
                "is_promoted": "premium"
            },
            {
                "title": "Will Ethereum ETF be approved in 2025?",
                "description": "Will the SEC approve a spot Ethereum ETF in the United States during 2025?",
                "category": "Crypto",
                "yes_odds": Decimal("58.00"),
                "no_odds": Decimal("42.00"),
                "is_promoted": "basic"
            },
            {
                "title": "Will Manchester City win the Premier League?",
                "description": "Prediction for the 2024/25 Premier League champion",
                "category": "Sports",
                "yes_odds": Decimal("65.00"),
                "no_odds": Decimal("35.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will Trump win 2024 US Election?",
                "description": "Presidential election prediction for 2024",
                "category": "Politics",
                "yes_odds": Decimal("52.00"),
                "no_odds": Decimal("48.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will Tesla stock reach $300 in 2025?",
                "description": "Will Tesla (TSLA) stock price exceed $300 per share in 2025?",
                "category": "Finance",
                "yes_odds": Decimal("45.00"),
                "no_odds": Decimal("55.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will AI replace 10% of jobs by 2026?",
                "description": "Will artificial intelligence replace at least 10% of current jobs by end of 2026?",
                "category": "Technology",
                "yes_odds": Decimal("38.00"),
                "no_odds": Decimal("62.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will Russia-Ukraine war end in 2025?",
                "description": "Will there be a peace agreement or ceasefire between Russia and Ukraine in 2025?",
                "category": "Politics",
                "yes_odds": Decimal("30.00"),
                "no_odds": Decimal("70.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will Apple release AR glasses in 2025?",
                "description": "Will Apple officially announce and release AR/VR glasses in 2025?",
                "category": "Technology",
                "yes_odds": Decimal("25.00"),
                "no_odds": Decimal("75.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will Dogecoin reach $1 in 2025?",
                "description": "Will Dogecoin (DOGE) cryptocurrency reach $1 USD price in 2025?",
                "category": "Crypto",
                "yes_odds": Decimal("15.00"),
                "no_odds": Decimal("85.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will SpaceX land humans on Mars by 2027?",
                "description": "Will SpaceX successfully land humans on Mars surface by end of 2027?",
                "category": "Space",
                "yes_odds": Decimal("20.00"),
                "no_odds": Decimal("80.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will Real Madrid win Champions League 2024/25?",
                "description": "Prediction for UEFA Champions League 2024/25 winner",
                "category": "Sports",
                "yes_odds": Decimal("42.00"),
                "no_odds": Decimal("58.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will inflation in US drop below 2% in 2025?",
                "description": "Will US inflation rate (CPI) drop below 2% at any point in 2025?",
                "category": "Economics",
                "yes_odds": Decimal("55.00"),
                "no_odds": Decimal("45.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will TON reach $10 in 2025?",
                "description": "Will Toncoin (TON) cryptocurrency reach $10 USD price in 2025?",
                "category": "Crypto",
                "yes_odds": Decimal("48.00"),
                "no_odds": Decimal("52.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will new iPhone 16 have USB-C?",
                "description": "Will Apple's iPhone 16 feature USB-C charging port?",
                "category": "Technology",
                "yes_odds": Decimal("95.00"),
                "no_odds": Decimal("5.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will oil prices exceed $100/barrel in 2025?",
                "description": "Will WTI crude oil price exceed $100 per barrel at any point in 2025?",
                "category": "Economics",
                "yes_odds": Decimal("35.00"),
                "no_odds": Decimal("65.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will Messi retire from football in 2025?",
                "description": "Will Lionel Messi announce retirement from professional football in 2025?",
                "category": "Sports",
                "yes_odds": Decimal("22.00"),
                "no_odds": Decimal("78.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will global temperature increase by 1.5°C by 2026?",
                "description": "Will average global temperature rise reach 1.5°C above pre-industrial levels by 2026?",
                "category": "Climate",
                "yes_odds": Decimal("68.00"),
                "no_odds": Decimal("32.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will a new pandemic occur in 2025?",
                "description": "Will WHO declare a new pandemic (not COVID-19) in 2025?",
                "category": "Health",
                "yes_odds": Decimal("12.00"),
                "no_odds": Decimal("88.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will Barbie 2 movie be released in 2025?",
                "description": "Will Warner Bros release a Barbie sequel movie in 2025?",
                "category": "Entertainment",
                "yes_odds": Decimal("40.00"),
                "no_odds": Decimal("60.00"),
                "is_promoted": "none"
            },
            {
                "title": "Will quantum computer break Bitcoin encryption by 2027?",
                "description": "Will a quantum computer successfully break Bitcoin's encryption by end of 2027?",
                "category": "Technology",
                "yes_odds": Decimal("5.00"),
                "no_odds": Decimal("95.00"),
                "is_promoted": "none"
            }
        ]

        for market_data in markets_data:
            market = Market(
                **market_data,
                status=MarketStatus.OPEN,
                created_by=admin.id,
                resolve_date=datetime.utcnow() + timedelta(days=180)
            )
            session.add(market)

        await session.flush()
        print(f"✅ Created {len(markets_data)} markets\n")

        # Create missions
        print("Creating missions...")

        missions_data = [
            {
                "title": "First Bet",
                "description": "Make your first bet on any market",
                "reward_amount": Decimal("100.00"),
                "reward_currency": "PRED",
                "type": "achievement",
                "requirements": {"bets_count": 1}
            },
            {
                "title": "3 Bets Today",
                "description": "Make 3 bets in a single day",
                "reward_amount": Decimal("300.00"),
                "reward_currency": "PRED",
                "type": "daily",
                "requirements": {"daily_bets": 3}
            },
            {
                "title": "First Win",
                "description": "Win your first bet",
                "reward_amount": Decimal("200.00"),
                "reward_currency": "PRED",
                "type": "achievement",
                "requirements": {"wins_count": 1}
            },
            {
                "title": "Invite a Friend",
                "description": "Invite a friend using your referral code",
                "reward_amount": Decimal("1000.00"),
                "reward_currency": "PRED",
                "type": "achievement",
                "requirements": {"referrals_count": 1}
            },
            {
                "title": "10 Win Streak",
                "description": "Win 10 bets in a row",
                "reward_amount": Decimal("5000.00"),
                "reward_currency": "PRED",
                "type": "achievement",
                "requirements": {"win_streak": 10}
            }
        ]

        for mission_data in missions_data:
            mission = Mission(**mission_data, is_active=True)
            session.add(mission)

        await session.flush()
        print(f"✅ Created {len(missions_data)} missions\n")

        # Commit all changes
        await session.commit()

        print("✅ Database seeding completed successfully!\n")
        print("📊 Summary:")
        print(f"   - Users: 2")
        print(f"   - Markets: {len(markets_data)}")
        print(f"   - Missions: {len(missions_data)}")
        print("\n")


if __name__ == "__main__":
    asyncio.run(seed_database())
