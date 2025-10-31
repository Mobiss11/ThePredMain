from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import config


def get_main_menu() -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎯 Open App",
                web_app=WebAppInfo(url=config.WEBAPP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="💰 Balance", callback_data="balance"),
            InlineKeyboardButton(text="📊 Markets", callback_data="markets")
        ],
        [
            InlineKeyboardButton(text="🎁 Referral", callback_data="referral"),
            InlineKeyboardButton(text="❓ Help", callback_data="help")
        ]
    ])


def get_market_keyboard(market_id: int) -> InlineKeyboardMarkup:
    """Market action keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Bet YES", callback_data=f"bet_yes_{market_id}"),
            InlineKeyboardButton(text="❌ Bet NO", callback_data=f"bet_no_{market_id}")
        ],
        [
            InlineKeyboardButton(text="📊 Details", callback_data=f"market_details_{market_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Markets", callback_data="markets")
        ]
    ])


def get_bet_amount_keyboard(market_id: int, position: str) -> InlineKeyboardMarkup:
    """Bet amount selection keyboard"""
    amounts = [100, 500, 1000, 5000]
    keyboard = []

    row = []
    for amount in amounts:
        row.append(InlineKeyboardButton(
            text=f"{amount} PRED",
            callback_data=f"place_bet_{market_id}_{position}_{amount}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="⬅️ Back", callback_data=f"market_{market_id}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_balance_keyboard() -> InlineKeyboardMarkup:
    """Balance action keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Deposit TON", callback_data="deposit_ton"),
            InlineKeyboardButton(text="📜 History", callback_data="tx_history")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")
        ]
    ])
