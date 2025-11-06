"""
Leaderboard Period Model - История закрытых периодов
"""
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime


class PeriodType(str, enum.Enum):
    """Тип периода"""
    WEEK = "WEEK"
    MONTH = "MONTH"


class PeriodStatus(str, enum.Enum):
    """Статус периода"""
    ACTIVE = "ACTIVE"  # Текущий активный период
    CLOSED = "CLOSED"  # Закрыт и награды начислены
    SCHEDULED = "SCHEDULED"  # Запланирован к закрытию


class LeaderboardPeriod(Base):
    """История закрытых периодов лидерборда"""
    __tablename__ = "leaderboard_periods"

    id = Column(Integer, primary_key=True, index=True)
    period_type = Column(SQLEnum(PeriodType), nullable=False)  # week or month

    # Даты периода
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # Статус и награды
    status = Column(SQLEnum(PeriodStatus), default=PeriodStatus.ACTIVE, nullable=False)
    total_rewards_distributed = Column(Integer, default=0)  # Сумма всех выплаченных наград (deprecated, use ton/pred)
    total_ton_rewards = Column(Integer, default=0)  # Сумма наград в TON
    total_pred_rewards = Column(Integer, default=0)  # Сумма наград в PRED
    participants_count = Column(Integer, default=0)  # Количество участников
    winners_count = Column(Integer, default=0)  # Количество получивших награды

    # Когда был закрыт
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by_admin_id = Column(Integer, nullable=True)  # ID админа, если закрыл вручную

    # Автоматические поля
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<LeaderboardPeriod {self.period_type} {self.start_date} - {self.end_date} ({self.status})>"
