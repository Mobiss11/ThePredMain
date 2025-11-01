from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiohttp
from config import config
import os

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command - Show welcome message with photo"""
    user = message.from_user

    # Register user via API (silently, no error shown to user)
    async with aiohttp.ClientSession() as session:
        try:
            auth_data = {
                "telegram_id": user.id,
                "first_name": user.first_name,
                "username": user.username,
                "last_name": user.last_name
            }

            async with session.post(
                f"{config.API_URL}/auth/register",
                json=auth_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pred_balance = data.get("pred_balance", 10000)
                else:
                    pred_balance = 10000  # Default value if registration fails
        except:
            pred_balance = 10000  # Default value if API unavailable

    # Welcome message
    welcome_text = f"""<b>🔮 Добро пожаловать в ThePred!</b>

Привет, {user.first_name}!

<b>🎯 Что такое ThePred?</b>
ThePred — это платформа для предсказания будущего, где ты можешь делать прогнозы на реальные события и получать вознаграждение за точность.

<b>💡 Как это работает:</b>
• Выбирай интересующее событие
• Делай прогноз: ДА или НЕТ
• Используй PRED токены или TON
• Получай награду, если угадал!

<b>🎁 Твой стартовый баланс:</b> {pred_balance:,.0f} PRED

<b>🚀 Начни сейчас:</b>
✓ Исследуй 20+ активных рынков
✓ Выполняй ежедневные миссии
✓ Приглашай друзей (+100 PRED за друга)
✓ Поднимайся в таблице лидеров

<i>Предскажи будущее — стань экспертом! 🔥</i>

Нажми кнопку ниже, чтобы открыть приложение 👇"""

    # Create webapp button
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🚀 Открыть ThePred",
        web_app=WebAppInfo(url=config.WEBAPP_URL)
    )

    # Send photo with welcome message
    photo_path = os.path.join(os.path.dirname(__file__), "..", "photo_2025-10-30_11-43-57.jpg")

    if os.path.exists(photo_path):
        photo = FSInputFile(photo_path)
        await message.answer_photo(
            photo=photo,
            caption=welcome_text,
            reply_markup=builder.as_markup()
        )
    else:
        # Fallback if photo not found
        await message.answer(
            welcome_text,
            reply_markup=builder.as_markup()
        )
