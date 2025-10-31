from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.inline import get_balance_keyboard
import aiohttp
from config import config

router = Router()


@router.message(Command("balance"))
@router.callback_query(F.data == "balance")
async def show_balance(event: Message | CallbackQuery):
    """Show user balance"""
    user_id = event.from_user.id

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{config.API_URL}/users/balance/{user_id}") as resp:
                if resp.status == 200:
                    balance = await resp.json()

                    text = f"""
💰 <b>Your Balance</b>

💎 PRED: <b>{balance['pred_balance']}</b>
🔷 TON: <b>{balance['ton_balance']}</b>

<i>Use PRED for practice bets or deposit TON for real money betting!</i>
"""

                    if isinstance(event, CallbackQuery):
                        await event.message.edit_text(
                            text,
                            reply_markup=get_balance_keyboard()
                        )
                        await event.answer()
                    else:
                        await event.answer(
                            text,
                            reply_markup=get_balance_keyboard()
                        )
                else:
                    error_text = "⚠️ Failed to load balance."
                    if isinstance(event, CallbackQuery):
                        await event.message.edit_text(error_text)
                        await event.answer()
                    else:
                        await event.answer(error_text)

        except Exception as e:
            error_text = "⚠️ Service temporarily unavailable."
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(error_text)
                await event.answer()
            else:
                await event.answer(error_text)


@router.callback_query(F.data == "deposit_ton")
async def show_deposit_info(callback: CallbackQuery):
    """Show deposit information"""
    # In production, generate unique deposit address
    deposit_address = "UQxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    text = f"""
➕ <b>Deposit TON</b>

Send TON to this address:
<code>{deposit_address}</code>

⚠️ <b>Important:</b>
• Minimum deposit: 1 TON
• Funds will be credited automatically
• Only send TON to this address

Your deposit will appear in your balance within 1-2 minutes.
"""

    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "tx_history")
async def show_transaction_history(callback: CallbackQuery):
    """Show transaction history"""
    user_id = callback.from_user.id

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{config.API_URL}/wallet/transactions/{user_id}?limit=10"
            ) as resp:
                if resp.status == 200:
                    transactions = await resp.json()

                    if not transactions:
                        text = "📜 <b>Transaction History</b>\n\nNo transactions yet."
                    else:
                        text = "📜 <b>Recent Transactions</b>\n\n"
                        for tx in transactions:
                            emoji = "➕" if tx['type'] in ['deposit', 'win', 'referral', 'mission'] else "➖"
                            text += f"{emoji} {tx['type'].upper()}\n"
                            text += f"   {tx['amount']} {tx['currency']}\n"
                            text += f"   {tx['status']} • {tx['created_at'][:10]}\n\n"

                    await callback.message.edit_text(text)
                else:
                    await callback.message.edit_text("⚠️ Failed to load transactions.")

        except Exception as e:
            await callback.message.edit_text("⚠️ Service temporarily unavailable.")

    await callback.answer()
