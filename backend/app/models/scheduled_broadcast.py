"""
Scheduled Broadcast Model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class BroadcastStatus(str, enum.Enum):
    """Статус запланированной рассылки"""
    PENDING = "PENDING"  # Ожидает отправки
    PROCESSING = "PROCESSING"  # В процессе создания уведомлений
    COMPLETED = "COMPLETED"  # Завершено
    CANCELLED = "CANCELLED"  # Отменено


class ScheduledBroadcast(Base):
    """Запланированные broadcast рассылки"""
    __tablename__ = "scheduled_broadcasts"

    id = Column(Integer, primary_key=True, index=True)

    # Сообщение
    message_text = Column(Text, nullable=False)
    parse_mode = Column(String(10), default="HTML")  # HTML или Markdown
    photo_url = Column(String(500), nullable=True)  # URL фото на S3

    # Получатели
    target = Column(String(20), default="all")  # "all" или "specific"
    target_telegram_id = Column(Integer, nullable=True)  # Если target="specific"

    # Расписание
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)  # Когда отправить (UTC)

    # Статус
    status = Column(SQLEnum(BroadcastStatus), default=BroadcastStatus.PENDING, nullable=False, index=True)

    # Статистика
    total_recipients = Column(Integer, default=0)  # Количество получателей
    sent_count = Column(Integer, default=0)  # Отправлено

    # Метаданные
    created_by = Column(Integer, nullable=True)  # ID админа (опционально)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)  # Когда обработано

    def __repr__(self):
        return f"<ScheduledBroadcast {self.id} at {self.scheduled_at} ({self.status})>"
