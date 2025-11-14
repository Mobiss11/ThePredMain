from sqlalchemy import Column, BigInteger, String, DECIMAL, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class WithdrawalStatus(str, enum.Enum):
    PENDING = "pending"           # Ожидает обработки админом
    PROCESSING = "processing"     # Админ обрабатывает
    COMPLETED = "completed"       # Успешно выполнена
    REJECTED = "rejected"         # Отклонена
    CANCELLED = "cancelled"       # Отменена пользователем


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    # Amount details
    pred_amount = Column(DECIMAL(20, 2), nullable=False)      # Сумма в PRED
    ton_amount = Column(DECIMAL(20, 8), nullable=True)        # Сумма в TON (calculated)

    # TON wallet address (user's)
    ton_address = Column(String(255), nullable=False)

    # Status
    status = Column(Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING, nullable=False, index=True)

    # Transaction details (after completion)
    tx_hash = Column(String(255), nullable=True, index=True)  # TON blockchain transaction hash

    # Admin notes
    admin_note = Column(Text, nullable=True)                   # Причина отклонения или заметки
    processed_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)  # Admin user ID

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)  # When admin processed
