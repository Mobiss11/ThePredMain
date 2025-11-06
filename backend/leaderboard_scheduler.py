#!/usr/bin/env python3
"""
Scheduler для автоматического закрытия периодов лидерборда

Запуск: python3 leaderboard_scheduler.py

Логика:
- Проверяет каждую минуту текущее время (UTC)
- Закрывает недельные периоды каждое воскресенье в 23:59 UTC
- Закрывает месячные периоды в последний день месяца в 23:59 UTC
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
import calendar

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.services.leaderboard_service import LeaderboardService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LeaderboardScheduler:
    """Scheduler для автоматического закрытия периодов"""

    def __init__(self):
        self.running = False
        self.check_interval = 60  # Проверяем каждую минуту

        # Флаги для предотвращения дублирования
        self.week_closed_today = False
        self.month_closed_today = False

        logger.info("📅 Leaderboard Scheduler инициализирован")

    async def start(self):
        """Запуск scheduler"""
        self.running = True
        logger.info("🚀 Запуск Leaderboard Scheduler")
        logger.info("🌍 Все операции выполняются по UTC времени")

        try:
            await self._schedule_loop()
        except KeyboardInterrupt:
            logger.info("⚠️ Получен сигнал остановки")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в scheduler: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("✅ Scheduler остановлен")

    async def _schedule_loop(self):
        """Основной цикл проверки времени"""
        while self.running:
            try:
                now_utc = datetime.now(timezone.utc)

                # Логируем текущее время каждый час
                if now_utc.minute == 0:
                    logger.info(f"⏰ Текущее время UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")

                # Проверяем нужно ли закрыть недельный период
                await self._check_weekly_period(now_utc)

                # Проверяем нужно ли закрыть месячный период
                await self._check_monthly_period(now_utc)

                # Ждем до следующей проверки
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ Ошибка в schedule loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Ждем минуту при ошибке

    async def _check_weekly_period(self, now_utc: datetime):
        """
        Проверить нужно ли закрыть недельный период

        Закрываем каждое воскресенье в 23:59 UTC
        """
        # Воскресенье = 6 (0 = понедельник, 6 = воскресенье)
        is_sunday = now_utc.weekday() == 6
        is_closing_time = now_utc.hour == 23 and now_utc.minute == 59

        if is_sunday and is_closing_time and not self.week_closed_today:
            logger.info("🏁 Время закрытия недельного периода!")

            try:
                async with AsyncSessionLocal() as db:
                    result = await LeaderboardService.close_period_and_calculate_rewards(
                        db=db,
                        period_type="week",
                        admin_id=None  # Автоматическое закрытие
                    )

                    if result.get("success"):
                        logger.info(f"✅ Недельный период закрыт: {result}")
                        logger.info(f"💰 Начислено {result['total_rewards']} PRED для {result['winners_count']} победителей")
                        logger.info(f"📨 Поставлено в очередь {result['notifications_queued']} уведомлений")

                        self.week_closed_today = True
                    else:
                        logger.error(f"❌ Ошибка закрытия недельного периода: {result.get('error')}")

            except Exception as e:
                logger.error(f"❌ Исключение при закрытии недельного периода: {e}", exc_info=True)

        # Сбрасываем флаг на следующий день
        if not is_sunday:
            self.week_closed_today = False

    async def _check_monthly_period(self, now_utc: datetime):
        """
        Проверить нужно ли закрыть месячный период

        Закрываем в последний день месяца в 23:59 UTC
        """
        # Проверяем последний ли это день месяца
        last_day_of_month = calendar.monthrange(now_utc.year, now_utc.month)[1]
        is_last_day = now_utc.day == last_day_of_month
        is_closing_time = now_utc.hour == 23 and now_utc.minute == 59

        if is_last_day and is_closing_time and not self.month_closed_today:
            logger.info("🏁 Время закрытия месячного периода!")

            try:
                async with AsyncSessionLocal() as db:
                    result = await LeaderboardService.close_period_and_calculate_rewards(
                        db=db,
                        period_type="month",
                        admin_id=None  # Автоматическое закрытие
                    )

                    if result.get("success"):
                        logger.info(f"✅ Месячный период закрыт: {result}")
                        logger.info(f"💰 Начислено {result['total_rewards']} PRED для {result['winners_count']} победителей")
                        logger.info(f"📨 Поставлено в очередь {result['notifications_queued']} уведомлений")

                        self.month_closed_today = True
                    else:
                        logger.error(f"❌ Ошибка закрытия месячного периода: {result.get('error')}")

            except Exception as e:
                logger.error(f"❌ Исключение при закрытии месячного периода: {e}", exc_info=True)

        # Сбрасываем флаг на следующий день
        if not is_last_day:
            self.month_closed_today = False


async def main():
    """Точка входа"""
    scheduler = LeaderboardScheduler()
    await scheduler.start()


if __name__ == "__main__":
    asyncio.run(main())
