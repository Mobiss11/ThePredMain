from sqlalchemy import Column, BigInteger, String, DECIMAL, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class BetPosition(str, enum.Enum):
    YES = "yes"
    NO = "no"


class BetCurrency(str, enum.Enum):
    PRED = "PRED"
    TON = "TON"


class BetStatus(str, enum.Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"


class Bet(Base):
    __tablename__ = "bets"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    market_id = Column(BigInteger, ForeignKey("markets.id"), nullable=False, index=True)

    position = Column(Enum(BetPosition), nullable=False)
    amount = Column(DECIMAL(20, 2), nullable=False)
    currency = Column(Enum(BetCurrency), nullable=False)
    odds = Column(DECIMAL(5, 2), nullable=False)
    potential_win = Column(DECIMAL(20, 2), nullable=False)

    status = Column(Enum(BetStatus), default=BetStatus.PENDING, nullable=False)
    payout = Column(DECIMAL(20, 2), default=0.00, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
