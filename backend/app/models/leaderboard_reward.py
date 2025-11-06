"""
Leaderboard Rewards Model
"""
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class RewardPeriod(str, enum.Enum):
    """Reward period types"""
    WEEK = "week"
    MONTH = "month"


class LeaderboardReward(Base):
    """Leaderboard reward configuration"""
    __tablename__ = "leaderboard_rewards"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(SQLEnum(RewardPeriod), nullable=False)  # week or month
    rank_from = Column(Integer, nullable=False)  # Starting rank (e.g., 1)
    rank_to = Column(Integer, nullable=False)    # Ending rank (e.g., 1 for 1st place, 3 for 1-3)
    reward_amount = Column(Integer, nullable=False)  # PRED reward
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        if self.rank_from == self.rank_to:
            return f"<LeaderboardReward {self.period} #{self.rank_from}: {self.reward_amount} PRED>"
        return f"<LeaderboardReward {self.period} #{self.rank_from}-{self.rank_to}: {self.reward_amount} PRED>"
