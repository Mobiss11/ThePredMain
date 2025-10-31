from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
import aiohttp
from config import config

router = Router()


@router.message(Command("referral"))
@router.callback_query(F.data == "referral")
async def show_referral(event: Message | CallbackQuery):
    """Show referral link"""
    user_id = event.from_user.id

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{config.API_URL}/users/profile/{user_id}") as resp:
                if resp.status == 200:
                    profile = await resp.json()
                    referral_code = profile.get('referral_code', 'N/A')

                    bot_username = "ThePredBot"  # Replace with actual bot username
                    referral_link = f"https://t.me/{bot_username}?start={referral_code}"

                    text = f"""
🎁 <b>Invite Friends & Earn!</b>

Share your referral link and get <b>1,000 PRED</b> for each friend who joins!

🔗 <b>Your referral link:</b>
<code>{referral_link}</code>

💰 <b>Your rewards:</b>
• You get: 1,000 PRED per referral
• Your friend gets: 1,000 PRED bonus

The more friends you invite, the more you earn!

Share now and start earning! 🚀
"""

                    if isinstance(event, CallbackQuery):
                        await event.message.edit_text(text)
                        await event.answer()
                    else:
                        await event.answer(text)
                else:
                    error_text = "⚠️ Failed to load referral info."
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
