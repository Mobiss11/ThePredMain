"""Initialize default missions in the database"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.mission import Mission
from app.core.database import engine, async_session
import asyncio


DEFAULT_MISSIONS = [
    {
        "title": "Первая Ставка",
        "description": "Сделай свою первую ставку на любое событие",
        "reward_amount": 500,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"bets_count": 1},
        "icon": "🎯"
    },
    {
        "title": "Новичок",
        "description": "Сделай 5 ставок на любые события",
        "reward_amount": 1000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"bets_count": 5},
        "icon": "🌟"
    },
    {
        "title": "Первая Победа",
        "description": "Выиграй свою первую ставку",
        "reward_amount": 750,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"wins_count": 1},
        "icon": "🏆"
    },
    {
        "title": "Серия Побед",
        "description": "Выиграй 3 ставки подряд",
        "reward_amount": 2000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"win_streak": 3},
        "icon": "🔥"
    },
    {
        "title": "Активный Трейдер",
        "description": "Сделай 10 ставок на любые события",
        "reward_amount": 2500,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"bets_count": 10},
        "icon": "💼"
    },
    {
        "title": "Любитель Крипты",
        "description": "Сделай 3 ставки на события категории Crypto",
        "reward_amount": 1500,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"category_bets": {"category": "Crypto", "count": 3}},
        "icon": "₿"
    },
    {
        "title": "Пригласи Друга",
        "description": "Пригласи 1 друга по реферальной ссылке",
        "reward_amount": 2000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"referrals_count": 1},
        "icon": "🎁"
    }
]


async def init_default_missions():
    """Initialize default missions if they don't exist"""
    async with async_session() as db:
        try:
            # Check if missions already exist
            result = await db.execute(select(Mission))
            existing_missions = result.scalars().all()

            if len(existing_missions) > 0:
                print(f"✓ Missions already exist ({len(existing_missions)} missions found)")
                return

            # Create default missions
            print("Creating default missions...")
            for mission_data in DEFAULT_MISSIONS:
                mission = Mission(
                    title=mission_data["title"],
                    description=mission_data["description"],
                    icon=mission_data.get("icon", "🎯"),
                    reward_amount=mission_data["reward_amount"],
                    reward_currency=mission_data["reward_currency"],
                    type=mission_data["type"],
                    requirements=mission_data["requirements"],
                    is_active=True
                )
                db.add(mission)

            await db.commit()
            print(f"✓ Created {len(DEFAULT_MISSIONS)} default missions")

        except Exception as e:
            print(f"✗ Error initializing missions: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    # Run this script directly to initialize missions
    asyncio.run(init_default_missions())
