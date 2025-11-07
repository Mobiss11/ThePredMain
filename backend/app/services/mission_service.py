"""Mission Service - Автоматическое обновление прогресса миссий"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.mission import Mission, UserMission
from app.models.user import User
from app.models.bet import Bet, BetStatus
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import logging
import aiohttp

logger = logging.getLogger(__name__)


class MissionService:
    """Сервис для управления миссиями и прогрессом"""

    @staticmethod
    async def update_user_mission_progress(
        db: AsyncSession,
        user_id: int,
        mission_id: int,
        progress: int,
        completed: bool = False
    ):
        """Обновить прогресс пользователя по миссии"""
        # Check if user mission exists
        result = await db.execute(
            select(UserMission).where(
                and_(
                    UserMission.user_id == user_id,
                    UserMission.mission_id == mission_id
                )
            )
        )
        user_mission = result.scalar_one_or_none()

        if user_mission:
            # Update existing
            user_mission.progress = progress
            if completed and not user_mission.completed:
                user_mission.completed = True
                user_mission.completed_at = datetime.now(timezone.utc)
        else:
            # Create new
            user_mission = UserMission(
                user_id=user_id,
                mission_id=mission_id,
                progress=progress,
                completed=completed,
                completed_at=datetime.now(timezone.utc) if completed else None
            )
            db.add(user_mission)

        await db.commit()
        return user_mission

    @staticmethod
    async def check_and_update_all_missions(db: AsyncSession, user_id: int):
        """Проверить и обновить все миссии пользователя"""
        # Get all active missions
        result = await db.execute(
            select(Mission).where(Mission.is_active == True)
        )
        missions = result.scalars().all()

        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return

        for mission in missions:
            await MissionService._check_mission_progress(db, user, mission)

    @staticmethod
    async def _check_mission_progress(db: AsyncSession, user: User, mission: Mission):
        """Проверить прогресс конкретной миссии"""
        requirements = mission.requirements
        progress = 0
        completed = False

        # Bets count
        if "bets_count" in requirements:
            target = requirements["bets_count"]
            progress = user.total_bets
            completed = progress >= target

        # Wins count
        elif "wins_count" in requirements:
            target = requirements["wins_count"]
            progress = user.total_wins
            completed = progress >= target

        # Win streak
        elif "win_streak" in requirements:
            target = requirements["win_streak"]
            progress = user.win_streak
            completed = progress >= target

        # Category bets
        elif "category_bets" in requirements:
            category_req = requirements["category_bets"]
            category = category_req["category"]
            target = category_req["count"]

            # Count bets in specific category
            from app.models.market import Market
            result = await db.execute(
                select(func.count(Bet.id))
                .join(Market, Bet.market_id == Market.id)
                .where(
                    and_(
                        Bet.user_id == user.id,
                        Market.category == category
                    )
                )
            )
            progress = result.scalar() or 0
            completed = progress >= target

        # Referrals count
        elif "referrals_count" in requirements:
            target = requirements["referrals_count"]
            # Count referred users (users who have this user as referrer)
            result = await db.execute(
                select(func.count(User.id)).where(User.referrer_id == user.id)
            )
            progress = result.scalar() or 0
            completed = progress >= target

        # Daily bets (reset daily)
        elif "daily_bets" in requirements:
            target = requirements["daily_bets"]
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            result = await db.execute(
                select(func.count(Bet.id)).where(
                    and_(
                        Bet.user_id == user.id,
                        Bet.created_at >= today_start
                    )
                )
            )
            progress = result.scalar() or 0
            completed = progress >= target

        # Weekly bets (reset weekly)
        elif "weekly_bets" in requirements:
            target = requirements["weekly_bets"]
            week_start = datetime.now(timezone.utc) - timedelta(days=7)
            result = await db.execute(
                select(func.count(Bet.id)).where(
                    and_(
                        Bet.user_id == user.id,
                        Bet.created_at >= week_start
                    )
                )
            )
            progress = result.scalar() or 0
            completed = progress >= target

        # Subscription (check via Telegram Bot API)
        elif "subscription" in requirements:
            if mission.channel_id and mission.channel_username:
                subscribed = await MissionService.check_channel_subscription(
                    user_id=user.telegram_id,
                    channel_id=mission.channel_id,
                    channel_username=mission.channel_username
                )
                progress = 1 if subscribed else 0
                completed = subscribed
            else:
                return  # Skip if channel info missing

        # Update user mission progress
        await MissionService.update_user_mission_progress(
            db=db,
            user_id=user.id,
            mission_id=mission.id,
            progress=progress,
            completed=completed
        )

    @staticmethod
    async def check_channel_subscription(
        user_id: int,
        channel_id: str,
        channel_username: str,
        bot_token: Optional[str] = None
    ) -> bool:
        """Проверить подписку пользователя на канал через Telegram Bot API"""
        if not bot_token:
            # Get bot token from env
            import os
            bot_token = os.getenv("BOT_TOKEN")

        if not bot_token:
            logger.error("BOT_TOKEN not found in environment")
            return False

        try:
            # Try by channel ID first
            url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
            params = {
                "chat_id": channel_id,
                "user_id": user_id
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            status = data["result"]["status"]
                            # Member, administrator, creator = subscribed
                            return status in ["member", "administrator", "creator"]

                    # Try with @username if ID failed
                    if channel_username:
                        params["chat_id"] = f"@{channel_username}"
                        async with session.get(url, params=params) as response2:
                            if response2.status == 200:
                                data = await response2.json()
                                if data.get("ok"):
                                    status = data["result"]["status"]
                                    return status in ["member", "administrator", "creator"]

            return False

        except Exception as e:
            logger.error(f"Error checking channel subscription: {e}")
            return False

    @staticmethod
    async def reset_daily_missions(db: AsyncSession):
        """Сбросить прогресс ежедневных миссий (вызывать по cron)"""
        # Get all daily missions
        result = await db.execute(
            select(Mission).where(
                and_(
                    Mission.type == "daily",
                    Mission.is_active == True
                )
            )
        )
        daily_missions = result.scalars().all()

        # Reset user progress for daily missions
        for mission in daily_missions:
            await db.execute(
                UserMission.__table__.delete().where(
                    UserMission.mission_id == mission.id
                )
            )

        await db.commit()
        logger.info(f"✅ Reset {len(daily_missions)} daily missions")

    @staticmethod
    async def reset_weekly_missions(db: AsyncSession):
        """Сбросить прогресс еженедельных миссий (вызывать по cron)"""
        # Get all weekly missions
        result = await db.execute(
            select(Mission).where(
                and_(
                    Mission.type == "weekly",
                    Mission.is_active == True
                )
            )
        )
        weekly_missions = result.scalars().all()

        # Reset user progress for weekly missions
        for mission in weekly_missions:
            await db.execute(
                UserMission.__table__.delete().where(
                    UserMission.mission_id == mission.id
                )
            )

        await db.commit()
        logger.info(f"✅ Reset {len(weekly_missions)} weekly missions")
