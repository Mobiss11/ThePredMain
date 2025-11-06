"""
Telegram Notifications Queue Service
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.orm import selectinload
from app.models.telegram_notification import TelegramNotification, NotificationStatus, NotificationType
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
import json


class TelegramQueueService:
    """Сервис для работы с очередью Telegram уведомлений"""

    @staticmethod
    async def add_notification(
        db: AsyncSession,
        telegram_id: int,
        message_text: str,
        notification_type: NotificationType,
        user_id: Optional[int] = None,
        parse_mode: str = "HTML",
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> TelegramNotification:
        """
        Добавить уведомление в очередь

        Args:
            db: Database session
            telegram_id: Telegram ID получателя
            message_text: Текст сообщения
            notification_type: Тип уведомления
            user_id: ID пользователя (опционально)
            parse_mode: Режим парсинга (HTML или Markdown)
            scheduled_at: Время отправки (если None - отправить сразу)
            metadata: Дополнительные данные в JSON формате
        """
        notification = TelegramNotification(
            telegram_id=telegram_id,
            user_id=user_id,
            message_text=message_text,
            parse_mode=parse_mode,
            notification_type=notification_type,
            status=NotificationStatus.PENDING,
            scheduled_at=scheduled_at,
            notification_metadata=json.dumps(metadata) if metadata else None
        )

        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        return notification

    @staticmethod
    async def get_pending_messages(
        db: AsyncSession,
        limit: int = 10,
        include_scheduled: bool = True
    ) -> List[TelegramNotification]:
        """
        Получить pending сообщения для отправки

        Args:
            db: Database session
            limit: Максимальное количество сообщений
            include_scheduled: Включить запланированные сообщения, время которых наступило

        Returns:
            Список сообщений для отправки
        """
        now = datetime.now(timezone.utc)

        # Базовый запрос - pending сообщения
        query = select(TelegramNotification).where(
            TelegramNotification.status == NotificationStatus.PENDING
        )

        if include_scheduled:
            # Включаем сообщения, которые либо не запланированы, либо время наступило
            query = query.where(
                or_(
                    TelegramNotification.scheduled_at.is_(None),
                    TelegramNotification.scheduled_at <= now
                )
            )
        else:
            # Только не запланированные
            query = query.where(TelegramNotification.scheduled_at.is_(None))

        # Сортируем по дате создания (FIFO)
        query = query.order_by(TelegramNotification.created_at).limit(limit)

        # FOR UPDATE SKIP LOCKED - блокируем строки, пропускаем заблокированные
        query = query.with_for_update(skip_locked=True)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def mark_processing(
        db: AsyncSession,
        message_id: int
    ) -> None:
        """Отметить сообщение как обрабатываемое"""
        result = await db.execute(
            select(TelegramNotification).where(TelegramNotification.id == message_id)
        )
        message = result.scalar_one_or_none()

        if message:
            message.status = NotificationStatus.PROCESSING
            message.processing_at = datetime.now(timezone.utc)
            message.attempts += 1
            await db.commit()

    @staticmethod
    async def mark_sent(
        db: AsyncSession,
        message_id: int
    ) -> None:
        """Отметить сообщение как отправленное"""
        result = await db.execute(
            select(TelegramNotification).where(TelegramNotification.id == message_id)
        )
        message = result.scalar_one_or_none()

        if message:
            message.status = NotificationStatus.SENT
            message.sent_at = datetime.now(timezone.utc)
            await db.commit()

    @staticmethod
    async def mark_failed(
        db: AsyncSession,
        message_id: int,
        error_message: str,
        permanent_failure: bool = False
    ) -> None:
        """
        Отметить сообщение как failed

        Args:
            db: Database session
            message_id: ID сообщения
            error_message: Текст ошибки
            permanent_failure: Если True - не делать retry
        """
        result = await db.execute(
            select(TelegramNotification).where(TelegramNotification.id == message_id)
        )
        message = result.scalar_one_or_none()

        if message:
            if permanent_failure or message.attempts >= message.max_attempts:
                message.status = NotificationStatus.PERMANENT_FAILURE
            else:
                message.status = NotificationStatus.PENDING  # Вернуть в очередь для retry

            message.error_message = error_message
            message.last_error_at = datetime.now(timezone.utc)
            await db.commit()

    @staticmethod
    async def cleanup_old_messages(
        db: AsyncSession,
        days: int = 7
    ) -> int:
        """
        Удалить старые отправленные сообщения

        Args:
            db: Database session
            days: Удалить сообщения старше N дней

        Returns:
            Количество удаленных сообщений
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Удаляем только отправленные и permanent_failure
        result = await db.execute(
            delete(TelegramNotification).where(
                and_(
                    or_(
                        TelegramNotification.status == NotificationStatus.SENT,
                        TelegramNotification.status == NotificationStatus.PERMANENT_FAILURE
                    ),
                    TelegramNotification.created_at < cutoff_date
                )
            )
        )

        await db.commit()
        return result.rowcount

    @staticmethod
    async def get_queue_stats(db: AsyncSession) -> Dict:
        """Получить статистику очереди"""
        total_count = await db.scalar(
            select(func.count(TelegramNotification.id))
        )

        pending_count = await db.scalar(
            select(func.count(TelegramNotification.id)).where(
                TelegramNotification.status == NotificationStatus.PENDING
            )
        )

        processing_count = await db.scalar(
            select(func.count(TelegramNotification.id)).where(
                TelegramNotification.status == NotificationStatus.PROCESSING
            )
        )

        sent_count = await db.scalar(
            select(func.count(TelegramNotification.id)).where(
                TelegramNotification.status == NotificationStatus.SENT
            )
        )

        failed_count = await db.scalar(
            select(func.count(TelegramNotification.id)).where(
                TelegramNotification.status == NotificationStatus.FAILED
            )
        )

        return {
            "total": total_count or 0,
            "pending": pending_count or 0,
            "processing": processing_count or 0,
            "sent": sent_count or 0,
            "failed": failed_count or 0
        }
