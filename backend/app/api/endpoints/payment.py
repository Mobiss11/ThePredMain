"""
Payment API Endpoints

Handles:
- Creating payment invoices
- Payment history
- Webhook processing from CryptoCloud
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.payment import Payment
from app.services.cryptocloud_service import PaymentService
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payment"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class CreatePaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount in USD")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 10.0
            }
        }


class PaymentResponse(BaseModel):
    id: int
    invoice_id: str
    payment_url: str
    amount: float
    currency: str
    pred_amount: float | None  # Optional - not used for TON payments
    status: str
    created_at: str

    class Config:
        from_attributes = True


class PaymentHistoryResponse(BaseModel):
    id: int
    invoice_id: str | None
    amount: float
    currency: str
    pred_amount: float | None
    status: str
    payment_method: str
    created_at: str
    completed_at: str | None

    class Config:
        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/create/{user_id}", response_model=PaymentResponse)
async def create_payment(
    user_id: int,
    request: CreatePaymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new payment invoice

    - **amount**: Amount in USD (min: $1, max: $10,000)
    - Returns payment URL to redirect user to CryptoCloud

    Example:
    ```
    POST /api/payment/create
    {
        "amount": 10.0
    }
    ```

    Returns:
    ```
    {
        "id": 123,
        "invoice_id": "uuid-here",
        "payment_url": "https://cryptocloud.plus/pay/...",
        "amount": 10.0,
        "currency": "USD",
        "pred_amount": 100.0,
        "status": "pending",
        "created_at": "2025-11-14T12:00:00"
    }
    ```
    """
    try:
        payment_service = PaymentService(db)

        payment = await payment_service.create_payment(
            user_id=user_id,
            amount=request.amount,
            currency="USD"
        )

        return PaymentResponse(
            id=payment.id,
            invoice_id=payment.invoice_id,
            payment_url=payment.payment_url,
            amount=float(payment.amount),
            currency=payment.currency,
            pred_amount=float(payment.pred_amount) if payment.pred_amount else None,
            status=payment.status.value,
            created_at=payment.created_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create payment")


@router.get("/history/{user_id}", response_model=List[PaymentHistoryResponse])
async def get_payment_history(
    user_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's payment history

    - **limit**: Number of payments to return (default: 10, max: 50)

    Returns list of payments sorted by created_at (newest first)
    """
    try:
        if limit > 50:
            limit = 50

        payment_service = PaymentService(db)
        payments = await payment_service.get_user_payments(user_id, limit=limit)

        return [
            PaymentHistoryResponse(
                id=p.id,
                invoice_id=p.invoice_id,
                amount=float(p.amount),
                currency=p.currency,
                pred_amount=float(p.pred_amount) if p.pred_amount else None,
                status=p.status.value,
                payment_method=p.payment_method.value,
                created_at=p.created_at.isoformat(),
                completed_at=p.completed_at.isoformat() if p.completed_at else None
            )
            for p in payments
        ]

    except Exception as e:
        logger.error(f"Error getting payment history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get payment history")


@router.post("/callback")
async def payment_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Callback endpoint for CryptoCloud webhooks

    URL: https://thepred.tech/api/payment/callback

    This endpoint is called by CryptoCloud when payment status changes.
    It processes the payment and credits user's PRED balance.

    **Security**: CryptoCloud sends webhook data as form-data or JSON
    **Important**: Always return 200 status to prevent webhook retries

    Expected data:
    ```
    {
        "invoice_id": "uuid",
        "status": "success",
        "amount_crypto": "0.001",
        "currency": "BTC",
        ...
    }
    ```
    """
    try:
        logger.info("=" * 50)
        logger.info("📨 Received webhook from CryptoCloud")

        # Try to get data as form-data first
        try:
            form_data = await request.form()
            data = {key: form_data.get(key) for key in form_data}
            logger.info(f"📝 Form data: {data}")
        except Exception:
            # If not form-data, try JSON
            data = await request.json()
            logger.info(f"📝 JSON data: {data}")

        # Validate status
        if data.get("status") != "success":
            logger.warning(f"⚠️ Non-success status: {data.get('status')}")
            return {"status": "processed", "message": "Non-success status"}

        # Validate invoice_id
        if not data.get("invoice_id"):
            logger.error("❌ Missing invoice_id")
            return {"status": "processed", "message": "Missing invoice_id"}

        # Process payment
        payment_service = PaymentService(db)
        success = await payment_service.process_payment_webhook(data)

        if success:
            logger.info("✅ Payment processed successfully")
            return {"status": "success", "message": "Payment processed"}
        else:
            logger.warning("⚠️ Payment processing failed")
            return {"status": "processed", "message": "Processing failed"}

    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        # Return 200 even on error to prevent CryptoCloud from retrying
        return {"status": "error", "message": str(e)}


@router.get("/successful-payment")
async def successful_payment():
    """
    Success redirect page after payment

    URL: https://thepred.tech/api/payment/successful-payment

    User is redirected here by CryptoCloud after successful payment.
    This is just a confirmation page - actual processing happens in callback webhook.
    """
    return {
        "status": "success",
        "message": "Payment completed! Your PRED balance will be updated shortly.",
        "redirect": "/profile"
    }


@router.get("/failed-payment")
async def failed_payment():
    """
    Failed redirect page after payment failure

    URL: https://thepred.tech/api/payment/failed-payment

    User is redirected here by CryptoCloud if payment fails or is cancelled.
    """
    return {
        "status": "error",
        "message": "Payment was not completed. Please try again.",
        "redirect": "/profile"
    }
