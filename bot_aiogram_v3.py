
import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from dotenv import load_dotenv


API_TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(text="🔥 Получить платную схему")],
        [
            types.KeyboardButton(text="💬 Оставить отзыв"),
            types.KeyboardButton(text="❓ Возникли трудности")
        ]
    ])
    return keyboard

@dp.message(CommandStart())
async def start_cmd(message: Message):
    user_id = str(message.from_user.id)
    users = load_users()

    if user_id not in users:
        users[user_id] = True
        save_users(users)
        await message.answer(
            "🎉 Добро пожаловать!\n\n"
            "Вот твоя бесплатная схема заработка с телефона:\n"
            "👉 https://casinoactionplay.com/FKMF\n\n"
            "Если хочешь больше — нажми кнопку ниже 👇",
            reply_markup=main_keyboard()
        )
    else:
        await message.answer(
            "⚠️ Ты уже получил бесплатную схему.\n\n"
            "Хочешь узнать больше? Получи доступ к полной версии схемы 👇",
            reply_markup=main_keyboard()
        )

@dp.message(lambda msg: msg.text == "🔥 Получить платную схему")
async def paid_scheme(message: Message):
    await message.answer(
        "🔐 Платная схема — это:\n"
        "- Полный пошаговый план\n"
        "- Фильтр от халявщиков\n"
        "- Твоя инвестиция в результат\n\n"
        "👉 Напиши мне в ЛС, чтобы получить её: @your_username"
    )

@dp.message(lambda msg: msg.text == "💬 Оставить отзыв")
async def leave_review(message: Message):
    await message.answer("📝 Напиши свой отзыв прямо сюда: @your_username")

@dp.message(lambda msg: msg.text == "❓ Возникли трудности")
async def faq_handler(message: Message):
    await message.answer(
        "❓ Частые вопросы и помощь:\n"
        "1. Не открывается ссылка? Попробуй открыть в другом браузере или включить VPN.\n"
        "2. Ничего не понятно? Напиши мне: @your_username\n\n"
        "Или загляни в помощника: @faq_helper_bot"
    )


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
