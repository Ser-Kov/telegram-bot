
import logging
import json
import os
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Простейшее хранилище пользователей (в JSON)
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    users = load_users()

    if user_id not in users:
        users[user_id] = True
        save_users(users)
        await message.answer(
            "🎉 Добро пожаловать!

Вот твоя бесплатная схема заработка с телефона:
"
            "👉 https://casinoactionplay.com/FKMF

"
            "Если хочешь больше — нажми кнопку ниже 👇",
            reply_markup=main_keyboard()
        )
    else:
        await message.answer(
            "⚠️ Ты уже получил бесплатную схему.

"
            "Хочешь узнать больше? Получи доступ к полной версии схемы 👇",
            reply_markup=main_keyboard()
        )

def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🔥 Получить платную схему")
    keyboard.add("💬 Оставить отзыв", "❓ Возникли трудности")
    return keyboard

@dp.message_handler(lambda msg: msg.text == "🔥 Получить платную схему")
async def paid_scheme(message: types.Message):
    await message.answer(
        "🔐 Платная схема — это:
"
        "- Полный пошаговый план
"
        "- Фильтр от халявщиков
"
        "- Твоя инвестиция в результат

"
        "👉 Напиши мне в ЛС, чтобы получить её: @your_username"
    )

@dp.message_handler(lambda msg: msg.text == "💬 Оставить отзыв")
async def leave_review(message: types.Message):
    await message.answer("📝 Напиши свой отзыв прямо сюда: @your_username")

@dp.message_handler(lambda msg: msg.text == "❓ Возникли трудности")
async def faq_handler(message: types.Message):
    await message.answer(
        "❓ Частые вопросы и помощь:
"
        "1. Не открывается ссылка? Открой в другом браузере.
"
        "2. Не понял схему? Напиши: @your_username

"
        "Или загляни в нашего помощника: @faq_helper_bot"
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
