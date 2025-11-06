"""Initialize default missions in the database"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.mission import Mission
from app.core.database import engine, AsyncSessionLocal
import asyncio


DEFAULT_MISSIONS = [
    # DAILY MISSIONS
    {
        "title": "Ежедневная Ставка",
        "description": "Сделай 3 ставки сегодня",
        "reward_amount": 500,
        "reward_currency": "PRED",
        "type": "daily",
        "requirements": {"daily_bets": 3},
        "icon": "🎯"
    },
    {
        "title": "Победа Дня",
        "description": "Выиграй хотя бы 1 ставку сегодня",
        "reward_amount": 1000,
        "reward_currency": "PRED",
        "type": "daily",
        "requirements": {"wins_count": 1},
        "icon": "🏆"
    },
    {
        "title": "Ежедневный Вход",
        "description": "Просто зайди в приложение сегодня",
        "reward_amount": 100,
        "reward_currency": "PRED",
        "type": "daily",
        "requirements": {"bets_count": 0},
        "icon": "📅"
    },

    # WEEKLY MISSIONS
    {
        "title": "Недельный Марафон",
        "description": "Сделай 20 ставок за неделю",
        "reward_amount": 5000,
        "reward_currency": "PRED",
        "type": "weekly",
        "requirements": {"weekly_bets": 20},
        "icon": "📊"
    },
    {
        "title": "Мастер Недели",
        "description": "Выиграй 10 ставок за неделю",
        "reward_amount": 10000,
        "reward_currency": "PRED",
        "type": "weekly",
        "requirements": {"wins_count": 10},
        "icon": "🌟"
    },
    {
        "title": "Огненная Серия",
        "description": "Выиграй 5 ставок подряд",
        "reward_amount": 15000,
        "reward_currency": "PRED",
        "type": "weekly",
        "requirements": {"win_streak": 5},
        "icon": "🔥"
    },

    # ACHIEVEMENTS
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
        "icon": "🌱"
    },
    {
        "title": "Первая Победа",
        "description": "Выиграй свою первую ставку",
        "reward_amount": 750,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"wins_count": 1},
        "icon": "🥇"
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
        "icon": "📈"
    },
    {
        "title": "Ветеран",
        "description": "Сделай 50 ставок",
        "reward_amount": 10000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"bets_count": 50},
        "icon": "🎖️"
    },
    {
        "title": "Легенда",
        "description": "Сделай 100 ставок",
        "reward_amount": 25000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"bets_count": 100},
        "icon": "🏅"
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
        "title": "Спортивный Фанат",
        "description": "Сделай 3 ставки на спортивные события",
        "reward_amount": 1500,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"category_bets": {"category": "Sports", "count": 3}},
        "icon": "⚽"
    },
    {
        "title": "Политический Эксперт",
        "description": "Сделай 3 ставки на политические события",
        "reward_amount": 1500,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"category_bets": {"category": "Politics", "count": 3}},
        "icon": "🗳️"
    },
    {
        "title": "Пригласи Друга",
        "description": "Пригласи 1 друга по реферальной ссылке",
        "reward_amount": 2000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"referrals_count": 1},
        "icon": "👥"
    },
    {
        "title": "Коллекционер Побед",
        "description": "Выиграй 25 ставок",
        "reward_amount": 20000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"wins_count": 25},
        "icon": "🎁"
    },
    {
        "title": "Неудержимый",
        "description": "Выиграй 10 ставок подряд",
        "reward_amount": 50000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"win_streak": 10},
        "icon": "🚀"
    }
]


async def init_default_missions():
    """Initialize default missions if they don't exist"""
    async with AsyncSessionLocal() as db:
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
