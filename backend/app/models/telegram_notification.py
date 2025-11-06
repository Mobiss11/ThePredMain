"""
Telegram Notifications Queue Model
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, Enum as SQLEnum, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime


class NotificationStatus(str, enum.Enum):
    """Статус уведомления"""
    PENDING = "pending"  # Ожидает отправки
    PROCESSING = "processing"  # В процессе отправки
    SENT = "sent"  # Успешно отправлено
    FAILED = "failed"  # Ошибка отправки (будет retry)
    PERMANENT_FAILURE = "permanent_failure"  # Необратимая ошибка (не делать retry)


class NotificationType(str, enum.Enum):
    """Тип уведомления"""
    LEADERBOARD_REWARD = "leaderboard_reward"  # Награда за место в лидерборде
    MARKET_RESOLVED = "market_resolved"  # Рынок разрешен
    BET_WON = "bet_won"  # Ставка выиграла
    BET_LOST = "bet_lost"  # Ставка проиграла
    MISSION_COMPLETED = "mission_completed"  # Миссия выполнена
    SYSTEM = "system"  # Системное уведомление


class TelegramNotification(Base):
    """Очередь Telegram уведомлений"""
    __tablename__ = "telegram_notifications_queue"

    id = Column(Integer, primary_key=True, index=True)

    # Получатель
    telegram_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Может быть NULL для некоторых случаев

    # Сообщение
    message_text = Column(Text, nullable=False)
    parse_mode = Column(String(10), default="HTML")  # HTML или Markdown
    notification_type = Column(SQLEnum(NotificationType), nullable=False)

    # Статус отправки
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    attempts = Column(Integer, default=0)  # Количество попыток отправки
    max_attempts = Column(Integer, default=5)  # Максимум попыток

    # Планирование отправки
    scheduled_at = Column(DateTime(timezone=True), nullable=True)  # Когда нужно отправить
    processing_at = Column(DateTime(timezone=True), nullable=True)  # Когда началась обработка
    sent_at = Column(DateTime(timezone=True), nullable=True)  # Когда отправлено

    # Ошибки
    error_message = Column(Text, nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)

    # Метаданные
    notification_metadata = Column(Text, nullable=True)  # JSON для дополнительной информации

    # Автоматические поля
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<TelegramNotification {self.id} to {self.telegram_id} ({self.status})>"
