from sqlalchemy import Column, BigInteger, String, DECIMAL, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class PaymentMethod(str, enum.Enum):
    CRYPTOCLOUD = "cryptocloud"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    # CryptoCloud invoice
    invoice_id = Column(String(255), unique=True, nullable=True, index=True)
    payment_url = Column(String(1000), nullable=True)

    # Payment details
    amount = Column(DECIMAL(20, 2), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    crypto_amount = Column(DECIMAL(20, 8), nullable=True)  # Actual crypto paid
    crypto_currency = Column(String(10), nullable=True)  # BTC, ETH, USDT, etc.

    # Converted amount
    pred_amount = Column(DECIMAL(20, 2), nullable=True)  # Amount in PRED after conversion

    # Payment method & status
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CRYPTOCLOUD, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)

    # Metadata
    description = Column(String(500), nullable=True)
    payment_data = Column(Text, nullable=True)  # JSON data from CryptoCloud

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
