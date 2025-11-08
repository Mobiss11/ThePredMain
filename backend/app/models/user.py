from sqlalchemy import Column, BigInteger, String, DECIMAL, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)

    # Balances
    pred_balance = Column(DECIMAL(20, 2), default=1000.00, nullable=False)
    ton_balance = Column(DECIMAL(20, 2), default=0.00, nullable=False)

    # Gamification
    rank = Column(String(50), default="Bronze", nullable=False)
    total_bets = Column(BigInteger, default=0, nullable=False)
    total_wins = Column(BigInteger, default=0, nullable=False)
    total_losses = Column(BigInteger, default=0, nullable=False)
    win_streak = Column(BigInteger, default=0, nullable=False)

    # Referral
    referrer_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    referral_code = Column(String(50), unique=True, nullable=True)

    # Ban system
    is_banned = Column(Boolean, default=False, nullable=False)
    ban_reason = Column(Text, nullable=True)
    banned_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    # support_tickets = relationship("SupportTicket", back_populates="user")  # TODO: Create SupportTicket model
