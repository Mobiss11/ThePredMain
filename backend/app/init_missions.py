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
        "icon": "daily_bet"
    },
    {
        "title": "Победа Дня",
        "description": "Выиграй хотя бы 1 ставку сегодня",
        "reward_amount": 1000,
        "reward_currency": "PRED",
        "type": "daily",
        "requirements": {"wins_count": 1},
        "icon": "daily_win"
    },
    {
        "title": "Ежедневный Вход",
        "description": "Просто зайди в приложение сегодня",
        "reward_amount": 100,
        "reward_currency": "PRED",
        "type": "daily",
        "requirements": {"bets_count": 0},
        "icon": "daily_login"
    },

    # WEEKLY MISSIONS
    {
        "title": "Недельный Марафон",
        "description": "Сделай 20 ставок за неделю",
        "reward_amount": 5000,
        "reward_currency": "PRED",
        "type": "weekly",
        "requirements": {"weekly_bets": 20},
        "icon": "weekly_marathon"
    },
    {
        "title": "Мастер Недели",
        "description": "Выиграй 10 ставок за неделю",
        "reward_amount": 10000,
        "reward_currency": "PRED",
        "type": "weekly",
        "requirements": {"wins_count": 10},
        "icon": "weekly_master"
    },
    {
        "title": "Огненная Серия",
        "description": "Выиграй 5 ставок подряд",
        "reward_amount": 15000,
        "reward_currency": "PRED",
        "type": "weekly",
        "requirements": {"win_streak": 5},
        "icon": "fire_streak"
    },

    # ACHIEVEMENTS
    {
        "title": "Первая Ставка",
        "description": "Сделай свою первую ставку на любое событие",
        "reward_amount": 500,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"bets_count": 1},
        "icon": "first_bet"
    },
    {
        "title": "Новичок",
        "description": "Сделай 5 ставок на любые события",
        "reward_amount": 1000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"bets_count": 5},
        "icon": "beginner"
    },
    {
        "title": "Первая Победа",
        "description": "Выиграй свою первую ставку",
        "reward_amount": 750,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"wins_count": 1},
        "icon": "first_win"
    },
    {
        "title": "Серия Побед",
        "description": "Выиграй 3 ставки подряд",
        "reward_amount": 2000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"win_streak": 3},
        "icon": "win_streak"
    },
    {
        "title": "Активный Трейдер",
        "description": "Сделай 10 ставок на любые события",
        "reward_amount": 2500,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"bets_count": 10},
        "icon": "active_trader"
    },
    {
        "title": "Ветеран",
        "description": "Сделай 50 ставок",
        "reward_amount": 10000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"bets_count": 50},
        "icon": "veteran"
    },
    {
        "title": "Легенда",
        "description": "Сделай 100 ставок",
        "reward_amount": 25000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"bets_count": 100},
        "icon": "legend"
    },
    {
        "title": "Любитель Крипты",
        "description": "Сделай 3 ставки на события категории Crypto",
        "reward_amount": 1500,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"category_bets": {"category": "Crypto", "count": 3}},
        "icon": "crypto_lover"
    },
    {
        "title": "Спортивный Фанат",
        "description": "Сделай 3 ставки на спортивные события",
        "reward_amount": 1500,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"category_bets": {"category": "Sports", "count": 3}},
        "icon": "sports_fan"
    },
    {
        "title": "Политический Эксперт",
        "description": "Сделай 3 ставки на политические события",
        "reward_amount": 1500,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"category_bets": {"category": "Politics", "count": 3}},
        "icon": "politics_expert"
    },
    {
        "title": "Пригласи Друга",
        "description": "Пригласи 1 друга по реферальной ссылке",
        "reward_amount": 2000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"referrals_count": 1},
        "icon": "referral"
    },
    {
        "title": "Коллекционер Побед",
        "description": "Выиграй 25 ставок",
        "reward_amount": 20000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"wins_count": 25},
        "icon": "collector"
    },
    {
        "title": "Неудержимый",
        "description": "Выиграй 10 ставок подряд",
        "reward_amount": 50000,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"win_streak": 10},
        "icon": "unstoppable"
    },
    {
        "title": "Подключи Кошелек",
        "description": "Подключи TON кошелек к своему аккаунту",
        "reward_amount": 100,
        "reward_currency": "PRED",
        "type": "achievement",
        "requirements": {"wallet_connected": True},
        "icon": "wallet"
    }
]


async def init_default_missions():
    """Initialize default missions if they don't exist"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if missions already exist
            result = await db.execute(select(Mission))
            existing_missions = result.scalars().all()

            # If we have 20 missions, recreate all to include CONNECT_WALLET
            if len(existing_missions) >= 20:
                print(f"✓ Missions already exist ({len(existing_missions)} missions found)")
                return

            # Delete old missions if any exist
            if len(existing_missions) > 0:
                print(f"⚠️ Found {len(existing_missions)} old missions, deleting...")

                # First delete all user_missions records that reference these missions
                from app.models.mission import UserMission
                mission_ids = [m.id for m in existing_missions]
                await db.execute(
                    UserMission.__table__.delete().where(
                        UserMission.mission_id.in_(mission_ids)
                    )
                )
                print(f"✓ Deleted user_missions records")

                # Now delete the missions themselves
                for mission in existing_missions:
                    await db.delete(mission)
                await db.commit()
                print(f"✓ Deleted {len(existing_missions)} old missions")

            # Create default missions
            print(f"Creating {len(DEFAULT_MISSIONS)} default missions...")
            for mission_data in DEFAULT_MISSIONS:
                mission = Mission(
                    title=mission_data["title"],
                    description=mission_data["description"],
                    icon=mission_data.get("icon", "first_bet"),
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
