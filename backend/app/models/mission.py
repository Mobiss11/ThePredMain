from sqlalchemy import Column, BigInteger, String, Text, DECIMAL, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Mission(Base):
    __tablename__ = "missions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    reward_amount = Column(DECIMAL(20, 2), nullable=False)
    reward_currency = Column(String(10), default="PRED", nullable=False)

    type = Column(String(50), nullable=False)  # daily, weekly, special, achievement
    requirements = Column(JSON, nullable=False)  # {"bets_count": 3} or {"wins_count": 1}

    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UserMission(Base):
    __tablename__ = "user_missions"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    mission_id = Column(BigInteger, ForeignKey("missions.id"), primary_key=True)

    progress = Column(Integer, default=0, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    claimed = Column(Boolean, default=False, nullable=False)

    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
