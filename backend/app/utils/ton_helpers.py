"""
TON Wallet Helper Functions

Утилиты для работы с TON:
- Конвертация TON ↔ PRED
- Валидация адресов
- Форматирование
"""

from decimal import Decimal
from typing import Tuple
from app.core.config import settings


def ton_to_pred(ton_amount: Decimal) -> int:
    """
    Конвертировать TON в PRED

    Args:
        ton_amount: Amount in TON

    Returns:
        Amount in PRED (integer)

    Example:
        >>> ton_to_pred(Decimal("1.5"))
        1500
    """
    return int(ton_amount * settings.TON_TO_PRED_RATE)


def pred_to_ton(pred_amount: int) -> Decimal:
    """
    Конвертировать PRED в TON

    Args:
        pred_amount: Amount in PRED

    Returns:
        Amount in TON (Decimal)

    Example:
        >>> pred_to_ton(1500)
        Decimal('1.5')
    """
    return Decimal(pred_amount) / Decimal(settings.TON_TO_PRED_RATE)


def validate_deposit_amount(amount: Decimal) -> Tuple[bool, str]:
    """
    Валидация суммы депозита

    Args:
        amount: Deposit amount in TON

    Returns:
        (is_valid, error_message)

    Example:
        >>> validate_deposit_amount(Decimal("0.05"))
        (False, "Minimum deposit: 0.1 TON")
    """
    min_deposit = Decimal(settings.MIN_DEPOSIT_TON)
    max_deposit = Decimal(settings.MAX_DEPOSIT_TON)

    if amount < min_deposit:
        return False, f"Minimum deposit: {min_deposit} TON"

    if amount > max_deposit:
        return False, f"Maximum deposit: {max_deposit} TON"

    return True, ""


def format_ton_amount(amount: Decimal, decimals: int = 2) -> str:
    """
    Форматировать сумму TON для отображения

    Args:
        amount: Amount in TON
        decimals: Number of decimal places

    Returns:
        Formatted string

    Example:
        >>> format_ton_amount(Decimal("1.5"))
        "1.50"
        >>> format_ton_amount(Decimal("0.001"), decimals=4)
        "0.0010"
    """
    return f"{amount:.{decimals}f}"


def format_pred_amount(amount: int) -> str:
    """
    Форматировать сумму PRED для отображения

    Args:
        amount: Amount in PRED

    Returns:
        Formatted string with thousands separator

    Example:
        >>> format_pred_amount(1500)
        "1,500"
        >>> format_pred_amount(1000000)
        "1,000,000"
    """
    return f"{amount:,}"


def is_valid_ton_address(address: str) -> bool:
    """
    Проверить валидность TON адреса

    TON addresses formats:
    - User-friendly: EQxxx... (48 chars, base64url)
    - Raw: 0:hex (64 hex chars)

    Args:
        address: TON wallet address

    Returns:
        True if valid

    Example:
        >>> is_valid_ton_address("EQD...")
        True
        >>> is_valid_ton_address("invalid")
        False
    """
    if not address or not isinstance(address, str):
        return False

    address = address.strip()

    # User-friendly format: EQ, UQ (mainnet), kQ (testnet)
    if address.startswith(('EQ', 'UQ', 'kQ')):
        # Should be exactly 48 characters
        if len(address) != 48:
            return False

        # Should be valid base64url
        import string
        valid_chars = string.ascii_letters + string.digits + '-_'
        return all(c in valid_chars for c in address[2:])

    # Raw format: workchain:address
    if ':' in address:
        try:
            workchain, addr_hex = address.split(':', 1)

            # Workchain should be -1 or 0
            if workchain not in ('-1', '0'):
                return False

            # Address should be 64 hex characters
            if len(addr_hex) != 64:
                return False

            # Validate hex
            int(addr_hex, 16)
            return True

        except (ValueError, AttributeError):
            return False

    return False


def shorten_address(address: str, start: int = 6, end: int = 4) -> str:
    """
    Сократить адрес для отображения

    Args:
        address: Full TON address
        start: Number of chars at start
        end: Number of chars at end

    Returns:
        Shortened address

    Example:
        >>> shorten_address("EQD1234567890abcdef...")
        "EQD123...cdef"
    """
    if not address or len(address) < start + end:
        return address

    return f"{address[:start]}...{address[-end:]}"


def calculate_deposit_fee(amount_ton: Decimal) -> Decimal:
    """
    Рассчитать комиссию депозита (если есть)

    Args:
        amount_ton: Deposit amount in TON

    Returns:
        Fee amount in TON

    Note:
        Сейчас комиссии нет, но можно добавить в будущем
    """
    # Пока без комиссии на депозит
    return Decimal("0")


def calculate_withdrawal_fee(amount_pred: int) -> int:
    """
    Рассчитать комиссию вывода

    Args:
        amount_pred: Withdrawal amount in PRED

    Returns:
        Fee amount in PRED

    Example:
        >>> calculate_withdrawal_fee(1000)
        50  # 5% commission
    """
    fee_rate = Decimal(settings.COMMISSION_TON)
    fee = int(amount_pred * fee_rate)
    return fee


def get_min_deposit_ton() -> Decimal:
    """Get minimum deposit amount in TON"""
    return Decimal(settings.MIN_DEPOSIT_TON)


def get_max_deposit_ton() -> Decimal:
    """Get maximum deposit amount in TON"""
    return Decimal(settings.MAX_DEPOSIT_TON)


def get_conversion_rate() -> int:
    """Get TON to PRED conversion rate"""
    return settings.TON_TO_PRED_RATE
