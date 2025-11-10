from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class WalletAddress(Base):
    """
    TON Wallet addresses connected to user accounts

    Users can connect their Telegram Wallet to deposit TON
    and convert to PRED tokens
    """
    __tablename__ = "wallet_addresses"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    # TON wallet address (user-friendly format)
    # Example: EQD...abc (48 chars)
    ton_address = Column(String(255), unique=True, nullable=False, index=True)

    # Raw address for API calls (optional)
    # Some APIs require raw format
    raw_address = Column(String(255), nullable=True)

    # Connection status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
