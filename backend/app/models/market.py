from sqlalchemy import Column, BigInteger, String, Text, DECIMAL, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class MarketStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class MarketOutcome(str, enum.Enum):
    YES = "yes"
    NO = "no"
    CANCELLED = "cancelled"


class ModerationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Market(Base):
    __tablename__ = "markets"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    photo_url = Column(String(500), nullable=True)
    moderation_status = Column(Enum(ModerationStatus), default=ModerationStatus.APPROVED, nullable=False)

    # Odds & Volume
    yes_odds = Column(DECIMAL(5, 2), default=50.00, nullable=False)
    no_odds = Column(DECIMAL(5, 2), default=50.00, nullable=False)
    total_volume_pred = Column(DECIMAL(20, 2), default=0.00, nullable=False)
    total_volume_ton = Column(DECIMAL(20, 2), default=0.00, nullable=False)

    # Yes/No pools
    yes_pool_pred = Column(DECIMAL(20, 2), default=0.00, nullable=False)
    no_pool_pred = Column(DECIMAL(20, 2), default=0.00, nullable=False)
    yes_pool_ton = Column(DECIMAL(20, 2), default=0.00, nullable=False)
    no_pool_ton = Column(DECIMAL(20, 2), default=0.00, nullable=False)

    # Status
    status = Column(Enum(MarketStatus), default=MarketStatus.OPEN, nullable=False)
    outcome = Column(Enum(MarketOutcome), nullable=True)

    # Dates
    resolve_date = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Meta
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)  # NULL for admin events
    views_count = Column(BigInteger, default=0, nullable=False)
    bets_count = Column(BigInteger, default=0, nullable=False)

    # Promotion
    is_promoted = Column(String(50), default="none", nullable=False)  # none, basic, premium
    promoted_until = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
