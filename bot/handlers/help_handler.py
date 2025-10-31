from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

router = Router()


@router.message(Command("help"))
@router.callback_query(F.data == "help")
async def show_help(event: Message | CallbackQuery):
    """Show help message"""
    text = """
❓ <b>ThePred Bot Help</b>

<b>Available Commands:</b>

/start - Start bot & register
/balance - Check your balance
/markets - View active markets
/bet - Place a quick bet
/referral - Get referral link
/help - Show this help

<b>How to Bet:</b>
1. Browse markets with /markets
2. Choose a market
3. Select YES or NO
4. Pick bet amount
5. Confirm bet

<b>Quick Bet:</b>
/bet <market_id> <yes/no> <amount>
Example: /bet 1 yes 1000

<b>Currencies:</b>
💎 PRED - Free practice token
🔷 TON - Real cryptocurrency

<b>Need more help?</b>
Contact support: @ThePredSupport
"""

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text)
        await event.answer()
    else:
        await event.answer(text)
