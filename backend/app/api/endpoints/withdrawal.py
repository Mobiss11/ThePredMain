"""
Withdrawal API Endpoints

Handles:
- Creating withdrawal requests
- Viewing user's withdrawal requests
- Admin: viewing all requests, processing (approve/reject)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List
from decimal import Decimal
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.withdrawal import WithdrawalRequest, WithdrawalStatus
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/withdrawal", tags=["withdrawal"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class CreateWithdrawalRequest(BaseModel):
    pred_amount: float = Field(..., gt=0, description="Amount in PRED to withdraw")
    ton_address: str = Field(..., min_length=10, max_length=255, description="TON wallet address")

    class Config:
        json_schema_extra = {
            "example": {
                "pred_amount": 1000.0,
                "ton_address": "EQD..."
            }
        }


class WithdrawalResponse(BaseModel):
    id: int
    pred_amount: float
    ton_amount: float | None
    ton_address: str
    status: str
    tx_hash: str | None
    admin_note: str | None
    created_at: str
    processed_at: str | None

    class Config:
        from_attributes = True


# ============================================================================
# User Endpoints
# ============================================================================

@router.post("/create/{user_id}", response_model=WithdrawalResponse)
async def create_withdrawal_request(
    user_id: int,
    request: CreateWithdrawalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new withdrawal request

    Requirements:
    - User must have connected TON wallet
    - Sufficient PRED balance
    - Minimum withdrawal: 100 PRED
    - Maximum withdrawal: user's balance

    Process:
    1. User creates request
    2. Admin reviews and approves/rejects
    3. If approved, admin sends TON manually
    4. Admin marks as completed with tx_hash
    """
    try:
        # Get user
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate amount
        MIN_WITHDRAWAL = 100
        pred_amount = Decimal(str(request.pred_amount))

        if pred_amount < MIN_WITHDRAWAL:
            raise HTTPException(
                status_code=400,
                detail=f"Минимальная сумма вывода: {MIN_WITHDRAWAL} PRED"
            )

        # Check user balance
        if user.pred_balance < pred_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно средств. Доступно: {float(user.pred_balance)} PRED"
            )

        # Check if user has pending withdrawal
        pending_query = select(WithdrawalRequest).where(
            WithdrawalRequest.user_id == user_id,
            or_(
                WithdrawalRequest.status == WithdrawalStatus.PENDING,
                WithdrawalRequest.status == WithdrawalStatus.PROCESSING
            )
        )
        result = await db.execute(pending_query)
        pending_withdrawal = result.scalars().first()

        if pending_withdrawal:
            raise HTTPException(
                status_code=400,
                detail="У вас уже есть активная заявка на вывод. Дождитесь её обработки."
            )

        # Calculate TON amount (1000 PRED = 1 TON, same as deposit rate)
        ton_amount = pred_amount / 1000

        # Create withdrawal request
        withdrawal = WithdrawalRequest(
            user_id=user_id,
            pred_amount=pred_amount,
            ton_amount=ton_amount,
            ton_address=request.ton_address,
            status=WithdrawalStatus.PENDING
        )

        db.add(withdrawal)

        # Deduct PRED from user balance immediately (hold funds)
        user.pred_balance -= pred_amount

        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            type=TransactionType.WITHDRAW,
            currency="PRED",
            amount=pred_amount,
            status=TransactionStatus.PENDING,
            description=f"Заявка на вывод #{withdrawal.id}: {float(pred_amount)} PRED → {float(ton_amount)} TON",
            ton_address=request.ton_address
        )
        db.add(transaction)

        await db.commit()
        await db.refresh(withdrawal)

        logger.info(f"✅ Withdrawal request created: ID={withdrawal.id}, User={user_id}, Amount={pred_amount} PRED")

        return WithdrawalResponse(
            id=withdrawal.id,
            pred_amount=float(withdrawal.pred_amount),
            ton_amount=float(withdrawal.ton_amount) if withdrawal.ton_amount else None,
            ton_address=withdrawal.ton_address,
            status=withdrawal.status.value,
            tx_hash=withdrawal.tx_hash,
            admin_note=withdrawal.admin_note,
            created_at=withdrawal.created_at.isoformat(),
            processed_at=withdrawal.processed_at.isoformat() if withdrawal.processed_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating withdrawal request: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка создания заявки")


@router.get("/my-requests/{user_id}", response_model=List[WithdrawalResponse])
async def get_my_withdrawal_requests(
    user_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's withdrawal request history

    Returns list of withdrawal requests sorted by created_at (newest first)
    """
    try:
        if limit > 50:
            limit = 50

        query = (
            select(WithdrawalRequest)
            .where(WithdrawalRequest.user_id == user_id)
            .order_by(WithdrawalRequest.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        withdrawals = result.scalars().all()

        return [
            WithdrawalResponse(
                id=w.id,
                pred_amount=float(w.pred_amount),
                ton_amount=float(w.ton_amount) if w.ton_amount else None,
                ton_address=w.ton_address,
                status=w.status.value,
                tx_hash=w.tx_hash,
                admin_note=w.admin_note,
                created_at=w.created_at.isoformat(),
                processed_at=w.processed_at.isoformat() if w.processed_at else None
            )
            for w in withdrawals
        ]

    except Exception as e:
        logger.error(f"Error getting withdrawal requests: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения заявок")


@router.post("/cancel/{user_id}/{withdrawal_id}")
async def cancel_withdrawal_request(
    user_id: int,
    withdrawal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel pending withdrawal request

    Only pending requests can be cancelled.
    Refunds PRED to user balance.
    """
    try:
        # Get withdrawal
        query = select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id)
        result = await db.execute(query)
        withdrawal = result.scalars().first()

        if not withdrawal:
            raise HTTPException(status_code=404, detail="Заявка не найдена")

        # Check ownership
        if withdrawal.user_id != user_id:
            raise HTTPException(status_code=403, detail="Нет доступа к этой заявке")

        # Check status
        if withdrawal.status != WithdrawalStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Нельзя отменить заявку со статусом: {withdrawal.status.value}"
            )

        # Get user
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Refund PRED
        user.pred_balance += withdrawal.pred_amount

        # Update withdrawal status
        withdrawal.status = WithdrawalStatus.CANCELLED
        withdrawal.processed_at = datetime.utcnow()

        # Update transaction
        tx_query = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.WITHDRAW,
            Transaction.status == TransactionStatus.PENDING
        ).order_by(Transaction.created_at.desc()).limit(1)
        tx_result = await db.execute(tx_query)
        transaction = tx_result.scalars().first()

        if transaction:
            transaction.status = TransactionStatus.FAILED
            transaction.description += " (отменена пользователем)"

        await db.commit()

        logger.info(f"✅ Withdrawal cancelled: ID={withdrawal_id}, User={user_id}")

        return {
            "status": "success",
            "message": "Заявка отменена. PRED возвращены на баланс."
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error cancelling withdrawal: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка отмены заявки")
