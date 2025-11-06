"""
Leaderboard Period Service - Управление периодами и расчет наград
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, case, desc
from app.models.leaderboard_period import LeaderboardPeriod, PeriodType, PeriodStatus
from app.models.leaderboard_reward import LeaderboardReward, RewardPeriod
from app.models.user import User
from app.models.bet import Bet, BetStatus
from app.models.telegram_notification import NotificationType
from app.services.telegram_queue_service import TelegramQueueService
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class LeaderboardService:
    """Сервис для работы с периодами лидерборда"""

    @staticmethod
    async def close_period_and_calculate_rewards(
        db: AsyncSession,
        period_type: str,  # "week" or "month"
        admin_id: Optional[int] = None
    ) -> Dict:
        """
        Закрыть текущий период и рассчитать награды

        Args:
            db: Database session
            period_type: Тип периода (week или month)
            admin_id: ID админа, если закрытие вручную

        Returns:
            Статистика: количество наград, сумма и т.д.
        """
        logger.info(f"🏁 Начинаем закрытие периода {period_type}")

        # 1. Определяем даты периода
        now = datetime.now(timezone.utc)

        if period_type == "week":
            reward_period = RewardPeriod.WEEK
            db_period_type = PeriodType.WEEK
        else:
            reward_period = RewardPeriod.MONTH
            db_period_type = PeriodType.MONTH

        # Находим последний закрытый период этого типа
        last_period_query = select(LeaderboardPeriod).where(
            and_(
                LeaderboardPeriod.period_type == db_period_type,
                LeaderboardPeriod.status == PeriodStatus.CLOSED
            )
        ).order_by(desc(LeaderboardPeriod.closed_at)).limit(1)

        last_period_result = await db.execute(last_period_query)
        last_period = last_period_result.scalar_one_or_none()

        if period_type == "week":
            # НЕДЕЛИ ВСЕГДА: Понедельник 00:00 - Воскресенье 23:59
            if last_period:
                # Следующий понедельник после закрытия предыдущего периода
                days_until_monday = (7 - last_period.end_date.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7  # Если закрыли в воскресенье, берем следующий понедельник
                start_date = last_period.end_date + timedelta(days=days_until_monday)
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                logger.info(f"📅 Следующий недельный период начинается с понедельника: {start_date}")
            else:
                # Начало текущей недели (понедельник)
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                logger.info(f"📅 Первый период недели, начало с понедельника: {start_date}")
        else:
            # МЕСЯЦЫ ВСЕГДА: 1-е число 00:00 - Последнее число 23:59
            if last_period:
                # 1-е число следующего месяца после закрытия предыдущего
                if last_period.end_date.month == 12:
                    # Если декабрь, переходим на январь следующего года
                    start_date = last_period.end_date.replace(year=last_period.end_date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    # Иначе просто следующий месяц
                    start_date = last_period.end_date.replace(month=last_period.end_date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
                logger.info(f"📅 Следующий месячный период начинается с 1-го числа: {start_date}")
            else:
                # Начало текущего месяца
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                logger.info(f"📅 Первый период месяца, начало с 1-го числа: {start_date}")

        end_date = now

        # 2. Получаем rewards configuration
        rewards_query = select(LeaderboardReward).where(
            and_(
                LeaderboardReward.period == reward_period,
                LeaderboardReward.is_active == True
            )
        ).order_by(LeaderboardReward.rank_from)

        result = await db.execute(rewards_query)
        rewards = result.scalars().all()

        if not rewards:
            logger.warning(f"⚠️ Нет настроенных наград для {period_type}")
            return {
                "success": False,
                "error": f"No rewards configured for {period_type}"
            }

        # 3. Рассчитываем leaderboard за период
        profit_subquery = (
            select(
                Bet.user_id,
                func.sum(
                    case(
                        (Bet.status == BetStatus.WON, Bet.payout - Bet.amount),
                        (Bet.status == BetStatus.LOST, -Bet.amount),
                        else_=Decimal("0.00")
                    )
                ).label("profit"),
                func.count().label("bets_count")
            )
            .where(and_(
                Bet.created_at >= start_date,
                Bet.created_at <= end_date
            ))
            .group_by(Bet.user_id)
            .subquery()
        )

        query = (
            select(
                User,
                func.coalesce(profit_subquery.c.profit, Decimal("0.00")).label("profit"),
                func.coalesce(profit_subquery.c.bets_count, 0).label("period_bets")
            )
            .outerjoin(profit_subquery, User.id == profit_subquery.c.user_id)
            .where(profit_subquery.c.bets_count > 0)
            .order_by(desc("profit"))
            .order_by(desc(User.total_wins))
        )

        result = await db.execute(query)
        leaderboard = result.all()

        if not leaderboard:
            logger.warning(f"⚠️ Нет участников в лидерборде за {period_type}")
            return {
                "success": False,
                "error": "No participants in leaderboard"
            }

        # 4. Начисляем награды и создаем уведомления
        total_rewards = 0
        total_ton_rewards = 0
        total_pred_rewards = 0
        winners_count = 0
        participants_count = len(leaderboard)

        for rank, (user, profit, period_bets) in enumerate(leaderboard, start=1):
            # Находим награду для этого rank
            reward_info = LeaderboardService._find_reward_for_rank(rank, rewards)

            if reward_info:
                reward_amount, currency = reward_info

                if reward_amount > 0:
                    # Начисляем награду на правильный баланс
                    if currency == "TON":
                        user.ton_balance += reward_amount
                        total_ton_rewards += reward_amount
                    else:  # PRED
                        user.pred_balance += reward_amount
                        total_pred_rewards += reward_amount

                    total_rewards += reward_amount
                    winners_count += 1

                    # Создаем уведомление
                    message = LeaderboardService._format_reward_notification(
                        rank=rank,
                        reward_amount=reward_amount,
                        currency=currency,
                        profit=profit,
                        period_type=period_type
                    )

                    await TelegramQueueService.add_notification(
                        db=db,
                        telegram_id=user.telegram_id,
                        user_id=user.id,
                        message_text=message,
                        notification_type=NotificationType.LEADERBOARD_REWARD,
                        parse_mode="HTML"
                    )

                    logger.info(f"💰 Награда {reward_amount} {currency} для {user.username or user.first_name} (rank #{rank})")

        # 5. Сохраняем период в историю
        period = LeaderboardPeriod(
            period_type=db_period_type,
            start_date=start_date,
            end_date=end_date,
            status=PeriodStatus.CLOSED,
            total_rewards_distributed=total_rewards,
            total_ton_rewards=total_ton_rewards,
            total_pred_rewards=total_pred_rewards,
            participants_count=participants_count,
            winners_count=winners_count,
            closed_at=now,
            closed_by_admin_id=admin_id
        )

        db.add(period)
        await db.commit()

        logger.info(f"✅ Период {period_type} закрыт. Награды: {total_ton_rewards} TON + {total_pred_rewards} PRED для {winners_count} пользователей")

        return {
            "success": True,
            "period_id": period.id,
            "period_type": period_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "participants_count": participants_count,
            "winners_count": winners_count,
            "total_rewards": total_rewards,
            "total_ton_rewards": total_ton_rewards,
            "total_pred_rewards": total_pred_rewards,
            "notifications_queued": winners_count
        }

    @staticmethod
    def _find_reward_for_rank(rank: int, rewards: List[LeaderboardReward]) -> Optional[Tuple[int, str]]:
        """Найти награду для конкретного rank

        Returns:
            Tuple[amount, currency] or None
        """
        for reward in rewards:
            if reward.rank_from <= rank <= reward.rank_to:
                return (reward.reward_amount, reward.currency)
        return None

    @staticmethod
    def _format_reward_notification(rank: int, reward_amount: int, currency: str, profit: Decimal, period_type: str) -> str:
        """Форматировать уведомление о награде"""
        period_text = "недельного" if period_type == "week" else "месячного"
        medal = ""

        if rank == 1:
            medal = "🥇"
        elif rank == 2:
            medal = "🥈"
        elif rank == 3:
            medal = "🥉"
        else:
            medal = "🏆"

        profit_text = f"+{profit:,.0f}" if profit >= 0 else f"{profit:,.0f}"

        # Emoji для валюты
        currency_emoji = "💎" if currency == "TON" else "💰"

        return f"""
{medal} <b>Поздравляем!</b>

Вы заняли <b>#{rank} место</b> в {period_text} лидерборде!

{currency_emoji} Ваша награда: <b>{reward_amount:,} {currency}</b>
📈 Ваш профит: <b>{profit_text} PRED</b>

Награда уже начислена на ваш баланс. Продолжайте в том же духе! 🚀

🌍 Все данные по UTC
""".strip()

    @staticmethod
    async def get_closed_periods(
        db: AsyncSession,
        period_type: Optional[str] = None,
        limit: int = 50
    ) -> List[LeaderboardPeriod]:
        """Получить список закрытых периодов"""
        query = select(LeaderboardPeriod).where(
            LeaderboardPeriod.status == PeriodStatus.CLOSED
        )

        if period_type:
            db_period_type = PeriodType.WEEK if period_type == "week" else PeriodType.MONTH
            query = query.where(LeaderboardPeriod.period_type == db_period_type)

        query = query.order_by(desc(LeaderboardPeriod.closed_at)).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_current_period_stats(
        db: AsyncSession,
        period_type: str  # "week" or "month"
    ) -> Dict:
        """Получить статистику текущего периода"""
        now = datetime.now(timezone.utc)

        if period_type == "week":
            start_date = now - timedelta(days=7)
        else:
            start_date = now - timedelta(days=30)

        # Считаем количество участников (пользователи со ставками)
        participants_count = await db.scalar(
            select(func.count(func.distinct(Bet.user_id)))
            .where(and_(
                Bet.created_at >= start_date,
                Bet.created_at <= now
            ))
        )

        # Считаем потенциальные награды
        rewards_query = select(LeaderboardReward).where(
            LeaderboardReward.period == (RewardPeriod.WEEK if period_type == "week" else RewardPeriod.MONTH),
            LeaderboardReward.is_active == True
        )
        result = await db.execute(rewards_query)
        rewards = result.scalars().all()

        potential_rewards = sum(
            reward.reward_amount * (reward.rank_to - reward.rank_from + 1)
            for reward in rewards
        )

        return {
            "period_type": period_type,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat(),
            "participants_count": participants_count or 0,
            "potential_rewards": potential_rewards,
            "rewards_configured": len(rewards)
        }
