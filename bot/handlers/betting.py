from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.inline import get_bet_amount_keyboard
import aiohttp
from config import config
import re

router = Router()


@router.message(Command("bet"))
async def cmd_bet(message: Message):
    """Quick bet command: /bet <market_id> <yes/no> <amount>"""
    try:
        parts = message.text.split()
        if len(parts) != 4:
            await message.answer(
                "⚠️ <b>Usage:</b> /bet <market_id> <yes/no> <amount>\n\n"
                "<b>Example:</b> /bet 1 yes 1000"
            )
            return

        market_id = int(parts[1])
        position = parts[2].lower()
        amount = float(parts[3])

        if position not in ["yes", "no"]:
            await message.answer("⚠️ Position must be 'yes' or 'no'")
            return

        if amount <= 0:
            await message.answer("⚠️ Amount must be positive")
            return

        # Place bet via API
        async with aiohttp.ClientSession() as session:
            bet_data = {
                "market_id": market_id,
                "position": position,
                "amount": amount,
                "currency": "PRED"
            }

            # In production, get user_id from auth
            user_id = message.from_user.id

            async with session.post(
                f"{config.API_URL}/bets?user_id={user_id}",
                json=bet_data
            ) as resp:
                if resp.status == 200:
                    bet = await resp.json()
                    await message.answer(
                        f"✅ <b>Bet placed successfully!</b>\n\n"
                        f"Position: {position.upper()}\n"
                        f"Amount: {amount} PRED\n"
                        f"Odds: {bet['odds']:.1f}%\n"
                        f"Potential win: {bet['potential_win']:.2f} PRED"
                    )
                else:
                    error = await resp.json()
                    await message.answer(f"⚠️ {error.get('detail', 'Failed to place bet')}")

    except ValueError:
        await message.answer("⚠️ Invalid bet format. Use: /bet <market_id> <yes/no> <amount>")
    except Exception as e:
        await message.answer("⚠️ Failed to place bet. Please try again.")


@router.callback_query(F.data.regexp(r"^bet_(yes|no)_(\d+)$"))
async def choose_bet_amount(callback: CallbackQuery):
    """Show bet amount selection"""
    match = re.match(r"^bet_(yes|no)_(\d+)$", callback.data)
    position = match.group(1)
    market_id = int(match.group(2))

    await callback.message.edit_text(
        f"💰 <b>Choose bet amount</b>\n\n"
        f"Position: {position.upper()}\n"
        f"Select amount in PRED:",
        reply_markup=get_bet_amount_keyboard(market_id, position)
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^place_bet_(\d+)_(yes|no)_(\d+)$"))
async def place_bet(callback: CallbackQuery):
    """Place bet with selected amount"""
    match = re.match(r"^place_bet_(\d+)_(yes|no)_(\d+)$", callback.data)
    market_id = int(match.group(1))
    position = match.group(2)
    amount = float(match.group(3))

    async with aiohttp.ClientSession() as session:
        bet_data = {
            "market_id": market_id,
            "position": position,
            "amount": amount,
            "currency": "PRED"
        }

        user_id = callback.from_user.id

        try:
            async with session.post(
                f"{config.API_URL}/bets?user_id={user_id}",
                json=bet_data
            ) as resp:
                if resp.status == 200:
                    bet = await resp.json()
                    await callback.message.edit_text(
                        f"✅ <b>Bet placed successfully!</b>\n\n"
                        f"Position: {position.upper()}\n"
                        f"Amount: {amount} PRED\n"
                        f"Odds: {bet['odds']:.1f}%\n"
                        f"Potential win: {bet['potential_win']:.2f} PRED\n\n"
                        f"Good luck! 🍀"
                    )
                else:
                    error = await resp.json()
                    await callback.message.edit_text(
                        f"⚠️ {error.get('detail', 'Failed to place bet')}"
                    )

        except Exception as e:
            await callback.message.edit_text("⚠️ Failed to place bet. Please try again.")

    await callback.answer()
