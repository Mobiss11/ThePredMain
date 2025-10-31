from sqlalchemy import Column, BigInteger, String, DECIMAL, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    BET = "bet"
    WIN = "win"
    REFERRAL = "referral"
    MISSION = "mission"
    PROMOTION = "promotion"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    type = Column(Enum(TransactionType), nullable=False)
    currency = Column(String(10), nullable=False)
    amount = Column(DECIMAL(20, 2), nullable=False)

    # TON specific
    tx_hash = Column(String(255), nullable=True)
    ton_address = Column(String(255), nullable=True)

    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)

    # Meta
    description = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
