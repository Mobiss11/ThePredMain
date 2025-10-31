from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiohttp
from config import config

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command - Register user and show webapp button"""
    user = message.from_user

    # Register/authenticate user via API
    async with aiohttp.ClientSession() as session:
        try:
            auth_data = {
                "telegram_id": user.id,
                "first_name": user.first_name,
                "username": user.username,
                "last_name": user.last_name
            }

            async with session.post(
                f"{config.API_URL}/auth/telegram",
                json=auth_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    welcome_text = f"""
🎉 <b>Welcome to ThePred!</b>

Hi {user.first_name}! 👋

💎 <b>What is ThePred?</b>
ThePred is a prediction market where you can bet on future events using PRED tokens or TON cryptocurrency.

🎯 <b>How it works:</b>
1. Browse markets and choose an event
2. Predict YES or NO
3. Place your bet
4. Win if you're right!

🎁 <b>Your starting balance:</b> 1,000 PRED

🚀 <b>Start now:</b>
• Browse 20+ active markets
• Complete daily missions
• Invite friends (1,000 PRED per referral)
• Climb the leaderboard

Click the button below to open ThePred app! 👇
"""

                    # Create webapp button
                    builder = InlineKeyboardBuilder()
                    builder.button(
                        text="🚀 Open ThePred",
                        web_app=WebAppInfo(url=config.WEBAPP_URL)
                    )

                    await message.answer(
                        welcome_text,
                        reply_markup=builder.as_markup()
                    )
                else:
                    await message.answer("⚠️ Registration failed. Please try again with /start")

        except Exception as e:
            await message.answer("⚠️ Service temporarily unavailable. Please try again later.")
