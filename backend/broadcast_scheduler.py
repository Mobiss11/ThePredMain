#!/usr/bin/env python3
"""
Broadcast Scheduler Service

Периодически проверяет scheduled_broadcasts и создает уведомления
для broadcasts, время которых пришло.

Запуск: python3 broadcast_scheduler.py
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.scheduled_broadcast import ScheduledBroadcast, BroadcastStatus
from app.models.user import User
from app.services.telegram_queue_service import TelegramQueueService
from app.models.telegram_notification import NotificationType

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BroadcastScheduler:
    """Scheduler для обработки запланированных рассылок"""

    def __init__(self):
        self.running = False
        self.check_interval = 60  # Проверка каждые 60 секунд
        logger.info("🕐 Broadcast Scheduler инициализирован")

    async def start(self):
        """Запуск scheduler"""
        self.running = True
        logger.info("🚀 Запуск Broadcast Scheduler")

        try:
            while self.running:
                await self._check_and_process_broadcasts()
                await asyncio.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("⚠️ Получен сигнал остановки")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в scheduler: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("✅ Scheduler остановлен")

    async def _check_and_process_broadcasts(self):
        """Проверить и обработать пришедшие broadcasts"""
        async with AsyncSessionLocal() as db:
            try:
                now = datetime.now(timezone.utc)

                # Получить все PENDING broadcasts, время которых пришло
                query = select(ScheduledBroadcast).where(
                    ScheduledBroadcast.status == BroadcastStatus.PENDING,
                    ScheduledBroadcast.scheduled_at <= now
                ).order_by(ScheduledBroadcast.scheduled_at)

                result = await db.execute(query)
                broadcasts = result.scalars().all()

                if not broadcasts:
                    logger.debug("📭 Нет broadcasts для отправки")
                    return

                logger.info(f"📬 Найдено {len(broadcasts)} broadcast(s) для обработки")

                for broadcast in broadcasts:
                    await self._process_broadcast(db, broadcast)

            except Exception as e:
                logger.error(f"❌ Ошибка при проверке broadcasts: {e}", exc_info=True)

    async def _process_broadcast(self, db, broadcast: ScheduledBroadcast):
        """
        Обработать один broadcast - создать уведомления в очереди

        Args:
            db: Database session
            broadcast: ScheduledBroadcast object
        """
        try:
            logger.info(f"📤 Обработка broadcast ID {broadcast.id}")

            # Отметить как PROCESSING
            broadcast.status = BroadcastStatus.PROCESSING
            broadcast.processed_at = datetime.now(timezone.utc)
            await db.commit()

            # Получить получателей
            if broadcast.target == "all":
                query = select(User.telegram_id, User.id)
                result = await db.execute(query)
                recipients = [(row[0], row[1]) for row in result.all()]
            else:
                # Specific user
                query = select(User.telegram_id, User.id).where(
                    User.telegram_id == broadcast.target_telegram_id
                )
                result = await db.execute(query)
                row = result.one_or_none()
                recipients = [(row[0], row[1])] if row else []

            if not recipients:
                logger.warning(f"⚠️ Broadcast {broadcast.id}: нет получателей")
                broadcast.status = BroadcastStatus.COMPLETED
                broadcast.total_recipients = 0
                await db.commit()
                return

            logger.info(f"📨 Создание {len(recipients)} уведомлений для broadcast {broadcast.id}")

            # Создать уведомления в очереди
            queued_count = 0
            for telegram_id, user_id in recipients:
                try:
                    metadata = {
                        "broadcast": True,
                        "scheduled_broadcast_id": broadcast.id,
                        "photo_url": broadcast.photo_url
                    }

                    await TelegramQueueService.add_notification(
                        db=db,
                        telegram_id=telegram_id,
                        message_text=broadcast.message_text,
                        notification_type=NotificationType.BROADCAST,
                        user_id=user_id,
                        parse_mode=broadcast.parse_mode,
                        metadata=metadata
                    )

                    queued_count += 1

                except Exception as e:
                    logger.error(f"❌ Ошибка создания уведомления для {telegram_id}: {e}")
                    continue

            # Обновить статистику
            broadcast.total_recipients = len(recipients)
            broadcast.sent_count = queued_count
            broadcast.status = BroadcastStatus.COMPLETED
            await db.commit()

            logger.info(f"✅ Broadcast {broadcast.id} завершен: {queued_count}/{len(recipients)} уведомлений")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки broadcast {broadcast.id}: {e}", exc_info=True)
            # Откатить статус обратно на PENDING если не удалось обработать
            broadcast.status = BroadcastStatus.PENDING
            broadcast.processing_at = None
            await db.commit()


async def main():
    """Точка входа"""
    scheduler = BroadcastScheduler()
    await scheduler.start()


if __name__ == "__main__":
    asyncio.run(main())
