from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel, field_validator

from app.core.database import get_db
from app.core.config import settings
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.user import User
from app.models.wallet import WalletAddress
from app.services.ton_service import TONService
from app.services.telegram_queue_service import TelegramQueueService
from app.models.telegram_notification import NotificationType
from app.utils.ton_helpers import (
    ton_to_pred,
    validate_deposit_amount,
    is_valid_ton_address,
    get_conversion_rate,
    get_min_deposit_ton,
    get_max_deposit_ton
)

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ============ Pydantic Models ============

class ConnectWalletRequest(BaseModel):
    ton_address: str

    @field_validator('ton_address')
    @classmethod
    def validate_address(cls, v):
        if not is_valid_ton_address(v):
            raise ValueError('Invalid TON address format')
        return v.strip()


class CreateDepositRequest(BaseModel):
    amount_ton: Decimal

    @field_validator('amount_ton')
    @classmethod
    def validate_amount(cls, v):
        is_valid, error = validate_deposit_amount(v)
        if not is_valid:
            raise ValueError(error)
        return v


class VerifyDepositRequest(BaseModel):
    transaction_id: int
    tx_hash: str


class WalletBalanceResponse(BaseModel):
    pred_balance: Decimal
    ton_balance: Decimal
    wallet_connected: bool
    ton_address: str | None = None


class DepositResponse(BaseModel):
    transaction_id: int
    deposit_address: str
    amount_ton: Decimal
    expected_pred: int
    conversion_rate: int
    expires_at: datetime


class VerifyDepositResponse(BaseModel):
    success: bool
    pred_credited: int
    new_pred_balance: Decimal
    new_ton_balance: Decimal


# ============ Endpoints ============

@router.post("/connect/{user_id}")
async def connect_wallet(
    user_id: int,
    data: ConnectWalletRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Подключить TON кошелек к аккаунту

    Telegram Wallet автоматически передает адрес через TON Connect
    """
    # Проверить что адрес еще не используется другим пользователем
    existing_wallet = await db.execute(
        select(WalletAddress).where(WalletAddress.ton_address == data.ton_address)
    )
    existing = existing_wallet.scalar_one_or_none()

    if existing and existing.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This wallet is already connected to another account"
        )

    # Проверить есть ли уже кошелек у пользователя
    user_wallet = await db.execute(
        select(WalletAddress).where(WalletAddress.user_id == user_id)
    )
    wallet = user_wallet.scalar_one_or_none()

    if wallet:
        # Обновить существующий кошелек
        wallet.ton_address = data.ton_address
        wallet.is_active = True
        wallet.updated_at = datetime.now()
        logger.info(f"Updated wallet for user {user_id}: {data.ton_address}")
    else:
        # Создать новый кошелек
        wallet = WalletAddress(
            user_id=user_id,
            ton_address=data.ton_address
        )
        db.add(wallet)
        logger.info(f"Connected new wallet for user {user_id}: {data.ton_address}")

    await db.commit()
    await db.refresh(wallet)

    return {
        "success": True,
        "address": wallet.ton_address,
        "message": "Wallet connected successfully"
    }


@router.post("/deposit/create", response_model=DepositResponse)
async def create_deposit(
    data: CreateDepositRequest,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Создать запрос на депозит

    Пользователь указывает сумму TON для депозита.
    Backend возвращает адрес для отправки и ожидаемую сумму PRED.
    """
    # Рассчитать PRED
    pred_amount = ton_to_pred(data.amount_ton)

    # Проверить что у платформы есть адрес для депозитов
    if not settings.TON_DEPOSIT_ADDRESS:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Deposit service temporarily unavailable"
        )

    # Создать pending транзакцию
    expires_at = datetime.now() + timedelta(minutes=settings.DEPOSIT_TIMEOUT_MINUTES)

    transaction = Transaction(
        user_id=user_id,
        type=TransactionType.DEPOSIT,
        currency="TON",
        amount=data.amount_ton,
        converted_amount=Decimal(pred_amount),
        deposit_address=settings.TON_DEPOSIT_ADDRESS,
        status=TransactionStatus.PENDING,
        expires_at=expires_at,
        description=f"Deposit {data.amount_ton} TON → {pred_amount} PRED"
    )

    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    logger.info(
        f"Created deposit request: user={user_id}, "
        f"amount={data.amount_ton} TON, tx_id={transaction.id}"
    )

    return DepositResponse(
        transaction_id=transaction.id,
        deposit_address=settings.TON_DEPOSIT_ADDRESS,
        amount_ton=data.amount_ton,
        expected_pred=pred_amount,
        conversion_rate=get_conversion_rate(),
        expires_at=expires_at
    )


@router.post("/deposit/verify", response_model=VerifyDepositResponse)
async def verify_deposit(
    data: VerifyDepositRequest,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Проверить депозит на blockchain

    Пользователь отправляет tx_hash после совершения транзакции.
    Backend проверяет на blockchain и начисляет PRED.
    """
    # Получить пользователя
    user_result = await db.execute(select(User).where(User.id == user_id))
    current_user = user_result.scalar_one_or_none()

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Получить транзакцию
    transaction = await db.get(Transaction, data.transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    if transaction.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if transaction.status != TransactionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction already processed with status: {transaction.status}"
        )

    # Проверить что транзакция не истекла
    if transaction.expires_at and datetime.now() > transaction.expires_at:
        transaction.status = TransactionStatus.FAILED
        transaction.description = "Deposit timeout expired"
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposit request expired. Please create a new one."
        )

    # Проверить на blockchain
    ton_service = TONService(
        api_url=settings.TON_API_URL,
        api_key=settings.TON_API_KEY if settings.TON_API_KEY else None
    )

    verification = await ton_service.verify_transaction(
        tx_hash=data.tx_hash,
        expected_destination=transaction.deposit_address,
        expected_amount=transaction.amount,
        tolerance=Decimal("0.01")  # 0.01 TON tolerance
    )

    if not verification["valid"]:
        error_msg = verification.get("error", "Transaction verification failed")
        logger.warning(
            f"Deposit verification failed: user={user_id}, "
            f"tx={data.transaction_id}, error={error_msg}"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verification failed: {error_msg}"
        )

    # Проверить что транзакция успешна
    if not verification.get("success", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction failed on blockchain"
        )

    # Начислить PRED и TON
    pred_amount = int(transaction.converted_amount)

    current_user.pred_balance += pred_amount
    current_user.ton_balance += transaction.amount

    # Обновить транзакцию
    transaction.status = TransactionStatus.COMPLETED
    transaction.tx_hash = data.tx_hash
    transaction.ton_address = verification.get("sender")
    transaction.confirmations = verification.get("confirmations", 1)
    transaction.completed_at = datetime.now()

    await db.commit()
    await db.refresh(current_user)

    logger.info(
        f"Deposit completed: user={user_id}, "
        f"amount={transaction.amount} TON, pred={pred_amount}"
    )

    # Отправить уведомление
    await TelegramQueueService.add_notification(
        db=db,
        telegram_id=current_user.telegram_id,
        message_text=(
            f"✅ <b>Депозит успешно зачислен!</b>\n\n"
            f"💎 TON: <b>+{transaction.amount}</b>\n"
            f"🪙 PRED: <b>+{pred_amount}</b>\n\n"
            f"Новый баланс: <b>{current_user.pred_balance}</b> PRED"
        ),
        notification_type=NotificationType.SYSTEM,
        user_id=user_id
    )

    return VerifyDepositResponse(
        success=True,
        pred_credited=pred_amount,
        new_pred_balance=current_user.pred_balance,
        new_ton_balance=current_user.ton_balance
    )


@router.get("/deposit/{transaction_id}/status")
async def get_deposit_status(
    transaction_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Проверить статус депозита (для polling)

    Frontend может периодически опрашивать этот endpoint
    для отображения статуса.
    """
    transaction = await db.get(Transaction, transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    if transaction.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return {
        "transaction_id": transaction.id,
        "status": transaction.status,
        "amount_ton": transaction.amount,
        "expected_pred": int(transaction.converted_amount) if transaction.converted_amount else 0,
        "tx_hash": transaction.tx_hash,
        "created_at": transaction.created_at,
        "completed_at": transaction.completed_at,
        "expires_at": transaction.expires_at,
        "expired": datetime.now() > transaction.expires_at if transaction.expires_at else False
    }


@router.get("/balance/{user_id}", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить баланс пользователя и информацию о подключенном кошельке
    """
    # Получить пользователя
    user_result = await db.execute(select(User).where(User.id == user_id))
    current_user = user_result.scalar_one_or_none()

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Проверить подключенный кошелек
    wallet_result = await db.execute(
        select(WalletAddress).where(
            WalletAddress.user_id == user_id,
            WalletAddress.is_active == True
        )
    )
    wallet = wallet_result.scalar_one_or_none()

    return WalletBalanceResponse(
        pred_balance=current_user.pred_balance,
        ton_balance=current_user.ton_balance,
        wallet_connected=wallet is not None,
        ton_address=wallet.ton_address if wallet else None
    )


@router.get("/info")
async def get_wallet_info():
    """
    Получить информацию о депозитах для пользователя

    Возвращает лимиты, курс конвертации и другую полезную информацию.
    """
    return {
        "conversion_rate": get_conversion_rate(),
        "min_deposit_ton": str(get_min_deposit_ton()),
        "max_deposit_ton": str(get_max_deposit_ton()),
        "deposit_timeout_minutes": settings.DEPOSIT_TIMEOUT_MINUTES,
        "platform_address": settings.TON_DEPOSIT_ADDRESS if settings.TON_DEPOSIT_ADDRESS else None
    }
