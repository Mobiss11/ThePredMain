#!/usr/bin/env python3
"""
Consumer для отправки Telegram уведомлений из очереди БД

Запуск: python3 telegram_worker.py

Цель: избежать spam filtering в Telegram за счет:
- Rate limiting: 0.5 секунды между сообщениями + пауза 5 секунд каждые 20 сообщений
- Дедупликация сообщений
- Graceful degradation при ошибках
- Retry логика с экспоненциальной задержкой
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
import traceback

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest, TelegramForbiddenError

from app.core.database import AsyncSessionLocal
from app.services.telegram_queue_service import TelegramQueueService
from app.models.telegram_notification import NotificationStatus
from app.core.config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Отключаем SQL логи (они спамят консоль)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)


class TelegramNotificationsConsumer:
    """Consumer для отправки Telegram уведомлений из БД очереди"""

    def __init__(self):
        # Получаем BOT_TOKEN из переменных окружения
        bot_token = os.getenv('BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')

        if not bot_token:
            raise ValueError("BOT_TOKEN or TELEGRAM_BOT_TOKEN environment variable is required")

        self.bot = Bot(token=bot_token)
        self.running = False

        # Rate limiting: счетчик отправленных сообщений
        self.messages_sent_counter = 0

        # Настройки (как в примере)
        self.delay_between_messages = 0.5  # Короткая задержка между всеми сообщениями
        self.batch_pause_every = 20        # Пауза после каждых N сообщений
        self.batch_pause_duration = 5      # Длительность паузы (секунды)

        self.batch_size = 10               # Количество сообщений для обработки за раз
        self.poll_interval = 1             # Интервал опроса БД (секунды)
        self.cleanup_interval = 3600       # Очистка старых сообщений каждый час

        logger.info("🚀 Telegram Notifications Consumer инициализирован")

    async def start(self):
        """Запуск consumer"""
        self.running = True
        logger.info("🚀 Запуск Telegram Notifications Consumer")

        # Запускаем очистку старых сообщений в фоне
        cleanup_task = asyncio.create_task(self._cleanup_loop())

        try:
            await self._process_loop()
        except KeyboardInterrupt:
            logger.info("⚠️ Получен сигнал остановки")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в consumer: {e}", exc_info=True)
        finally:
            self.running = False
            cleanup_task.cancel()
            await self.bot.session.close()
            logger.info("✅ Consumer остановлен")

    async def _process_loop(self):
        """Основной цикл обработки сообщений"""
        while self.running:
            try:
                async with AsyncSessionLocal() as db:
                    # Получаем pending сообщения с блокировкой строк
                    messages = await TelegramQueueService.get_pending_messages(
                        db=db,
                        limit=self.batch_size,
                        include_scheduled=True
                    )

                    if not messages:
                        # Нет сообщений, ждем
                        await asyncio.sleep(self.poll_interval)
                        continue

                    logger.info(f"📬 Получено {len(messages)} сообщений для обработки")

                    # Отмечаем все как PROCESSING в той же транзакции
                    for message in messages:
                        message.status = NotificationStatus.PROCESSING
                        message.processing_at = datetime.now(timezone.utc)
                        message.attempts += 1

                    await db.commit()

                    # Теперь можем обрабатывать сообщения без риска дублирования
                    for message in messages:
                        await self._process_message(message)

            except Exception as e:
                logger.error(f"❌ Ошибка в process loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Задержка перед повтором при ошибке

    async def _process_message(self, message):
        """
        Обработать одно сообщение

        Args:
            message: TelegramNotification object (уже помечен как PROCESSING)
        """
        async with AsyncSessionLocal() as db:
            try:
                # Определяем parse mode
                parse_mode = ParseMode.MARKDOWN if message.parse_mode == "Markdown" else ParseMode.HTML

                # Парсим metadata для проверки photo_url
                import json
                metadata = {}
                if message.notification_metadata:
                    try:
                        metadata = json.loads(message.notification_metadata)
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось распарсить metadata: {e}")

                photo_url = metadata.get('photo_url')

                # Если есть фото - отправляем через send_photo
                if photo_url:
                    logger.info(f"📸 Отправка сообщения с фото: {photo_url}")
                    await self.bot.send_photo(
                        chat_id=message.telegram_id,
                        photo=photo_url,
                        caption=message.message_text,
                        parse_mode=parse_mode
                    )
                else:
                    # Без фото - обычное текстовое сообщение
                    await self.bot.send_message(
                        chat_id=message.telegram_id,
                        text=message.message_text,
                        parse_mode=parse_mode
                    )

                # Отмечаем как sent
                await TelegramQueueService.mark_sent(db=db, message_id=message.id)

                logger.info(f"✅ Отправлено сообщение {message.id} для {message.telegram_id}")

                # Инкрементируем счетчик отправленных сообщений
                self.messages_sent_counter += 1

                # Короткая задержка между всеми сообщениями
                await asyncio.sleep(self.delay_between_messages)

                # Проверяем нужна ли более длинная пауза после N сообщений
                if self.messages_sent_counter % self.batch_pause_every == 0:
                    logger.info(f"⏸️ Пауза на {self.batch_pause_duration} секунд после {self.batch_pause_every} сообщений...")
                    await asyncio.sleep(self.batch_pause_duration)

            except TelegramRetryAfter as e:
                # Telegram просит подождать
                logger.warning(f"⏱️ Rate limit от Telegram: retry after {e.retry_after} секунд")

                # Планируем повторную отправку
                async with AsyncSessionLocal() as retry_db:
                    await TelegramQueueService.mark_failed(
                        db=retry_db,
                        message_id=message.id,
                        error_message=f"Rate limit: retry after {e.retry_after}s"
                    )

                # Ждем указанное время
                await asyncio.sleep(e.retry_after)

            except TelegramForbiddenError as e:
                # Пользователь заблокировал бота - НЕОБРАТИМАЯ ошибка
                logger.warning(f"❌ Пользователь {message.telegram_id} заблокировал бота")

                async with AsyncSessionLocal() as retry_db:
                    await TelegramQueueService.mark_failed(
                        db=retry_db,
                        message_id=message.id,
                        error_message=f"User blocked bot: {e}",
                        permanent_failure=True
                    )

            except TelegramBadRequest as e:
                # Плохой запрос - НЕОБРАТИМАЯ ошибка
                logger.error(f"❌ Bad request для сообщения {message.id}: {e}")

                async with AsyncSessionLocal() as retry_db:
                    await TelegramQueueService.mark_failed(
                        db=retry_db,
                        message_id=message.id,
                        error_message=f"Bad request: {e}",
                        permanent_failure=True
                    )

            except Exception as e:
                # Другие ошибки
                logger.error(f"❌ Ошибка отправки сообщения {message.id}: {e}")
                logger.error(traceback.format_exc())

                async with AsyncSessionLocal() as retry_db:
                    await TelegramQueueService.mark_failed(
                        db=retry_db,
                        message_id=message.id,
                        error_message=str(e)
                    )

    async def _cleanup_loop(self):
        """Периодическая очистка старых сообщений"""
        while self.running:
            try:
                await asyncio.sleep(self.cleanup_interval)

                async with AsyncSessionLocal() as db:
                    deleted_count = await TelegramQueueService.cleanup_old_messages(
                        db=db,
                        days=7  # Удаляем сообщения старше 7 дней
                    )

                    if deleted_count > 0:
                        logger.info(f"🧹 Очистка: удалено {deleted_count} старых сообщений")

                    # Логируем статистику очереди
                    stats = await TelegramQueueService.get_queue_stats(db=db)
                    logger.info(f"📊 Статистика очереди: {stats}")

            except Exception as e:
                logger.error(f"❌ Ошибка в cleanup loop: {e}", exc_info=True)


async def main():
    """Точка входа"""
    consumer = TelegramNotificationsConsumer()
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
