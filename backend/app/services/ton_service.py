"""
TON Blockchain Service

Интеграция с TON blockchain через TonAPI.io
Функционал:
- Проверка транзакций на blockchain
- Получение баланса кошельков
- Валидация адресов
"""

import aiohttp
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TONService:
    """
    Сервис для работы с TON blockchain через TonAPI

    TonAPI docs: https://docs.tonconsole.com/tonapi/api-v2
    """

    def __init__(self, api_url: str, api_key: Optional[str] = None):
        """
        Initialize TON Service

        Args:
            api_url: TonAPI endpoint (e.g., https://tonapi.io/v2)
            api_key: Optional API key for higher rate limits
        """
        self.base_url = api_url.rstrip('/')
        self.api_key = api_key

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with optional API key"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @staticmethod
    def nanoton_to_ton(nanoton: int) -> Decimal:
        """
        Convert nanotons to TON

        1 TON = 10^9 nanotons
        """
        return Decimal(nanoton) / Decimal(10**9)

    @staticmethod
    def ton_to_nanoton(ton: Decimal) -> int:
        """
        Convert TON to nanotons

        1 TON = 10^9 nanotons
        """
        return int(ton * Decimal(10**9))

    async def verify_transaction(
        self,
        tx_hash: str,
        expected_destination: str,
        expected_amount: Decimal,
        tolerance: Decimal = Decimal("0.01")
    ) -> Dict[str, Any]:
        """
        Проверить транзакцию на blockchain

        Args:
            tx_hash: Transaction hash (base64 encoded)
            expected_destination: Expected recipient address
            expected_amount: Expected amount in TON
            tolerance: Allowed difference in amount (default 0.01 TON)

        Returns:
            {
                "valid": bool,
                "amount": Decimal,
                "sender": str,
                "recipient": str,
                "timestamp": int,
                "confirmations": int,
                "success": bool,
                "error": Optional[str]
            }
        """
        try:
            # TonAPI endpoint для получения транзакции
            # Note: tx_hash должен быть в формате hash:lt:address
            # Для упрощения используем событие по хэшу

            url = f"{self.base_url}/events/{tx_hash}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 404:
                        return {
                            "valid": False,
                            "error": "Transaction not found on blockchain"
                        }

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"TonAPI error: {response.status} - {error_text}")
                        return {
                            "valid": False,
                            "error": f"TonAPI error: {response.status}"
                        }

                    data = await response.json()

                    # Parse transaction data
                    event = data.get("event", {})
                    actions = event.get("actions", [])

                    if not actions:
                        return {
                            "valid": False,
                            "error": "No actions found in transaction"
                        }

                    # Найти действие перевода TON
                    ton_transfer = None
                    for action in actions:
                        if action.get("type") == "TonTransfer":
                            ton_transfer = action.get("TonTransfer", {})
                            break

                    if not ton_transfer:
                        return {
                            "valid": False,
                            "error": "No TON transfer found in transaction"
                        }

                    # Извлечь данные
                    sender = ton_transfer.get("sender", {}).get("address", "")
                    recipient = ton_transfer.get("recipient", {}).get("address", "")
                    amount_nanoton = int(ton_transfer.get("amount", 0))
                    amount_ton = self.nanoton_to_ton(amount_nanoton)

                    timestamp = event.get("timestamp", 0)
                    is_successful = event.get("in_progress", True) == False

                    # Проверка получателя
                    if recipient.lower() != expected_destination.lower():
                        return {
                            "valid": False,
                            "error": f"Wrong recipient. Expected: {expected_destination}, Got: {recipient}",
                            "amount": amount_ton,
                            "sender": sender,
                            "recipient": recipient
                        }

                    # Проверка суммы (с учетом tolerance)
                    amount_diff = abs(amount_ton - expected_amount)
                    if amount_diff > tolerance:
                        return {
                            "valid": False,
                            "error": f"Amount mismatch. Expected: {expected_amount}, Got: {amount_ton}",
                            "amount": amount_ton,
                            "sender": sender,
                            "recipient": recipient
                        }

                    # Все проверки пройдены
                    return {
                        "valid": True,
                        "amount": amount_ton,
                        "sender": sender,
                        "recipient": recipient,
                        "timestamp": timestamp,
                        "confirmations": 1,  # TonAPI показывает только подтвержденные транзакции
                        "success": is_successful,
                        "error": None
                    }

        except aiohttp.ClientError as e:
            logger.error(f"Network error while verifying transaction: {e}")
            return {
                "valid": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error verifying transaction: {e}", exc_info=True)
            return {
                "valid": False,
                "error": f"Internal error: {str(e)}"
            }

    async def get_wallet_balance(self, address: str) -> Optional[Decimal]:
        """
        Получить баланс TON кошелька

        Args:
            address: TON wallet address (user-friendly or raw)

        Returns:
            Balance in TON or None if error
        """
        try:
            url = f"{self.base_url}/accounts/{address}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status != 200:
                        logger.error(f"Failed to get balance for {address}: {response.status}")
                        return None

                    data = await response.json()
                    balance_nanoton = int(data.get("balance", 0))

                    return self.nanoton_to_ton(balance_nanoton)

        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            return None

    async def get_account_info(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Получить информацию об аккаунте

        Args:
            address: TON wallet address

        Returns:
            Account information or None if error
        """
        try:
            url = f"{self.base_url}/accounts/{address}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()

                    return {
                        "address": data.get("address"),
                        "balance": self.nanoton_to_ton(int(data.get("balance", 0))),
                        "status": data.get("status"),
                        "is_wallet": data.get("is_wallet", False)
                    }

        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    @staticmethod
    def is_valid_ton_address(address: str) -> bool:
        """
        Базовая валидация TON адреса

        TON addresses:
        - User-friendly: EQ... (48 chars, base64url)
        - Raw: 0:hex (64 hex chars)

        Args:
            address: TON address to validate

        Returns:
            True if valid format
        """
        if not address:
            return False

        address = address.strip()

        # User-friendly format: EQ, UQ, kQ (testnet)
        if address.startswith(('EQ', 'UQ', 'kQ')):
            # Should be 48 characters (base64url encoded)
            return len(address) == 48

        # Raw format: 0:hex or -1:hex
        if ':' in address:
            parts = address.split(':')
            if len(parts) == 2:
                workchain, hex_part = parts
                # Workchain should be 0 or -1
                if workchain not in ('0', '-1'):
                    return False
                # Hex part should be 64 hex characters
                try:
                    int(hex_part, 16)
                    return len(hex_part) == 64
                except ValueError:
                    return False

        return False
