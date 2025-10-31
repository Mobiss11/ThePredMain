from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.user import User
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

router = APIRouter()


class DepositRequest(BaseModel):
    amount: Decimal
    tx_hash: str


class TransactionResponse(BaseModel):
    id: int
    type: str
    currency: str
    amount: Decimal
    status: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/deposit/{user_id}")
async def deposit_ton(
    user_id: int,
    deposit_data: DepositRequest,
    db: AsyncSession = Depends(get_db)
):
    """Deposit TON to account"""
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # TODO: Verify TON transaction on blockchain

    # Create transaction record
    transaction = Transaction(
        user_id=user_id,
        type=TransactionType.DEPOSIT,
        currency="TON",
        amount=deposit_data.amount,
        tx_hash=deposit_data.tx_hash,
        status=TransactionStatus.COMPLETED,
        description="TON deposit"
    )

    # Update user balance
    user.ton_balance += deposit_data.amount

    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    return {
        "success": True,
        "transaction_id": transaction.id,
        "new_balance": user.ton_balance
    }


@router.get("/transactions/{user_id}", response_model=list[TransactionResponse])
async def get_transactions(
    user_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get user transaction history"""
    query = select(Transaction).where(
        Transaction.user_id == user_id
    ).order_by(desc(Transaction.created_at)).limit(limit)

    result = await db.execute(query)
    transactions = result.scalars().all()

    return transactions
