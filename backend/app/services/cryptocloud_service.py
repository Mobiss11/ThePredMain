"""
CryptoCloud Payment Gateway Service

Handles:
- Creating payment invoices
- Checking payment status
- Processing webhooks
"""
import httpx
import json
import logging
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.user import User
from app.models.transaction import Transaction, TransactionType, TransactionStatus

logger = logging.getLogger(__name__)


class CryptoCloudService:
    """Service for interacting with CryptoCloud API"""

    def __init__(self):
        self.api_url = settings.CRYPTOCLOUD_API_URL
        self.api_key = settings.CRYPTOCLOUD_API_KEY
        self.shop_id = settings.CRYPTOCLOUD_SHOP_ID
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }

    async def create_invoice(
        self,
        amount: float,
        currency: str = "USD",
        order_id: str = None,
        success_url: str = None,
        fail_url: str = None
    ) -> Dict:
        """
        Create payment invoice in CryptoCloud

        Args:
            amount: Payment amount
            currency: Currency (USD, EUR, RUB)
            order_id: Internal order ID
            success_url: Redirect URL on success
            fail_url: Redirect URL on failure

        Returns:
            Dict with invoice_id and payment_url
        """
        try:
            url = f"{self.api_url}/invoice/create"

            payload = {
                "shop_id": self.shop_id,
                "amount": str(amount),
                "currency": currency,
            }

            if order_id:
                payload["order_id"] = order_id

            # Use WEBAPP_URL from settings
            base_url = settings.WEBAPP_URL
            payload["success_url"] = success_url or f"{base_url}/successful-payment"
            payload["fail_url"] = fail_url or f"{base_url}/failed-payment"

            logger.info(f"Creating CryptoCloud invoice: {payload}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )

                response.raise_for_status()
                data = response.json()

                logger.info(f"CryptoCloud invoice created: {data}")

                if data.get("status") == "success":
                    result = data.get("result", {})
                    return {
                        "invoice_id": result.get("uuid"),
                        "payment_url": result.get("link"),
                        "amount": result.get("amount"),
                        "currency": result.get("currency"),
                        "status": "success"
                    }
                else:
                    raise Exception(f"CryptoCloud error: {data.get('message', 'Unknown error')}")

        except httpx.HTTPStatusError as e:
            logger.error(f"CryptoCloud HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Payment gateway error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"CryptoCloud error: {str(e)}")
            raise

    async def check_invoice_status(self, invoice_id: str) -> Dict:
        """
        Check invoice status

        Args:
            invoice_id: Invoice UUID from CryptoCloud

        Returns:
            Dict with invoice status details
        """
        try:
            url = f"{self.api_url}/invoice/info"

            params = {
                "uuid": invoice_id
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )

                response.raise_for_status()
                data = response.json()

                if data.get("status") == "success":
                    return data.get("result", {})
                else:
                    raise Exception(f"Failed to get invoice status: {data.get('message')}")

        except Exception as e:
            logger.error(f"Error checking invoice status: {str(e)}")
            raise


class PaymentService:
    """Service for managing payments in database"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cryptocloud = CryptoCloudService()

    async def create_payment(
        self,
        user_id: int,
        amount: float,
        currency: str = "USD"
    ) -> Payment:
        """
        Create new payment and generate CryptoCloud invoice

        Args:
            user_id: User ID
            amount: Payment amount in USD
            currency: Payment currency

        Returns:
            Payment object with invoice_id and payment_url
        """
        try:
            # Validate amount
            if amount < settings.MIN_DEPOSIT_USD:
                raise ValueError(f"Minimum deposit is ${settings.MIN_DEPOSIT_USD}")
            if amount > settings.MAX_DEPOSIT_USD:
                raise ValueError(f"Maximum deposit is ${settings.MAX_DEPOSIT_USD}")

            # Create payment record
            # Note: We don't set pred_amount here - TON will be credited via webhook
            payment = Payment(
                user_id=user_id,
                amount=Decimal(str(amount)),
                currency=currency,
                status=PaymentStatus.PENDING,
                payment_method=PaymentMethod.CRYPTOCLOUD,
                pred_amount=None,  # Not used - payment credits TON balance
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )

            self.db.add(payment)
            await self.db.flush()  # Get payment ID

            # Create CryptoCloud invoice
            invoice_data = await self.cryptocloud.create_invoice(
                amount=amount,
                currency=currency,
                order_id=str(payment.id)
            )

            # Update payment with invoice data
            payment.invoice_id = invoice_data["invoice_id"]
            payment.payment_url = invoice_data["payment_url"]
            payment.payment_data = json.dumps(invoice_data)

            await self.db.commit()
            await self.db.refresh(payment)

            logger.info(f"Payment created: ID={payment.id}, invoice_id={payment.invoice_id}")

            return payment

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating payment: {str(e)}")
            raise

    async def get_payment_by_invoice_id(self, invoice_id: str) -> Optional[Payment]:
        """Get payment by CryptoCloud invoice ID"""
        query = select(Payment).where(Payment.invoice_id == invoice_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_user_payments(self, user_id: int, limit: int = 10) -> list[Payment]:
        """Get user's payment history"""
        query = (
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def process_payment_webhook(self, webhook_data: Dict) -> bool:
        """
        Process webhook from CryptoCloud

        Expected webhook data:
        {
            "invoice_id": "uuid",
            "amount_crypto": "0.001",
            "currency": "BTC",
            "status": "success",
            ...
        }

        Returns:
            True if processed successfully
        """
        try:
            invoice_id = webhook_data.get("invoice_id")
            status = webhook_data.get("status")

            if not invoice_id:
                logger.error("Webhook missing invoice_id")
                return False

            # Find payment
            payment = await self.get_payment_by_invoice_id(invoice_id)
            if not payment:
                logger.error(f"Payment not found for invoice_id: {invoice_id}")
                return False

            # Check if already processed
            if payment.status == PaymentStatus.COMPLETED:
                logger.info(f"Payment {payment.id} already completed")
                return True

            # Process based on status
            if status == "success":
                await self._complete_payment(payment, webhook_data)
                logger.info(f"Payment {payment.id} completed successfully")
                return True
            elif status in ["fail", "cancelled"]:
                payment.status = PaymentStatus.FAILED
                await self.db.commit()
                logger.info(f"Payment {payment.id} failed/cancelled")
                return True
            else:
                logger.warning(f"Unknown payment status: {status}")
                return False

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            await self.db.rollback()
            return False

    async def _complete_payment(self, payment: Payment, webhook_data: Dict):
        """Complete payment and credit user balance"""
        try:
            # Update payment
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()
            payment.crypto_amount = Decimal(str(webhook_data.get("amount_crypto", 0)))
            payment.crypto_currency = webhook_data.get("currency", "")
            payment.payment_data = json.dumps(webhook_data)

            # Get user
            query = select(User).where(User.id == payment.user_id)
            result = await self.db.execute(query)
            user = result.scalars().first()

            if not user:
                raise Exception(f"User {payment.user_id} not found")

            # Credit TON balance (not PRED!)
            # Calculate TON amount from USD (approximate rate, actual from CryptoCloud)
            ton_amount = Decimal(str(float(payment.amount) * settings.USD_TO_TON_RATE))
            user.ton_balance += ton_amount

            # Create transaction record
            transaction = Transaction(
                user_id=user.id,
                type=TransactionType.DEPOSIT,
                currency="TON",
                amount=ton_amount,
                status=TransactionStatus.COMPLETED,
                description=f"CryptoCloud deposit: ${payment.amount} USDT → {ton_amount} TON",
                completed_at=datetime.utcnow()
            )
            self.db.add(transaction)

            await self.db.commit()

            logger.info(f"User {user.id} credited {ton_amount} TON (Payment {payment.id})")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error completing payment: {str(e)}")
            raise
