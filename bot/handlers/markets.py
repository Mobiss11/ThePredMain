from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.inline import get_market_keyboard
import aiohttp
from config import config

router = Router()


@router.message(Command("markets"))
@router.callback_query(F.data == "markets")
async def show_markets(event: Message | CallbackQuery):
    """Show top markets"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{config.API_URL}/markets?limit=5") as resp:
                if resp.status == 200:
                    markets = await resp.json()

                    if not markets:
                        text = "📊 No active markets available right now."
                    else:
                        text = "📊 <b>Top Active Markets</b>\n\n"
                        for i, market in enumerate(markets, 1):
                            text += f"{i}. <b>{market['title']}</b>\n"
                            text += f"   YES: {market['yes_odds']:.1f}% | NO: {market['no_odds']:.1f}%\n"
                            text += f"   Volume: {market['total_volume_pred']} PRED\n"
                            text += f"   /market_{market['id']}\n\n"

                    if isinstance(event, CallbackQuery):
                        await event.message.edit_text(text)
                        await event.answer()
                    else:
                        await event.answer(text)
                else:
                    error_text = "⚠️ Failed to load markets. Please try again."
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


@router.message(F.text.regexp(r"^/market_(\d+)$"))
async def show_market_details(message: Message):
    """Show market details"""
    market_id = int(message.text.split("_")[1])

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{config.API_URL}/markets/{market_id}") as resp:
                if resp.status == 200:
                    market = await resp.json()

                    text = f"""
📊 <b>{market['title']}</b>

{market['description'] or 'No description'}

📈 <b>Current Odds:</b>
✅ YES: {market['yes_odds']:.1f}%
❌ NO: {market['no_odds']:.1f}%

💰 <b>Total Volume:</b>
{market['total_volume_pred']} PRED
{market['total_volume_ton']} TON

👥 <b>Total Bets:</b> {market['bets_count']}
👁 <b>Views:</b> {market['views_count']}

Place your bet now! 👇
"""

                    await message.answer(
                        text,
                        reply_markup=get_market_keyboard(market_id)
                    )
                else:
                    await message.answer("⚠️ Market not found.")

        except Exception as e:
            await message.answer("⚠️ Failed to load market details.")
