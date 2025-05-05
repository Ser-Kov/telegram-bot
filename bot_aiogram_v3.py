from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
import os

API_TOKEN = os.environ.get("BOT_TOKEN")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# --- Кнопки --- #
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("📄 Скачать PDF"))
main_menu.add(KeyboardButton("💳 Купить 50+ промптов"))
main_menu.add(KeyboardButton("✨ Индивидуальные промпты"))

# --- Хендлеры --- #
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.answer(
        "Привет! 👋\n\nЯ помогу тебе использовать нейросети эффективно. Получи бесплатный PDF с 10 промптами и начни прямо сейчас!",
        reply_markup=main_menu
    )

@dp.message_handler(lambda message: message.text == "📄 Скачать PDF")
async def send_pdf(message: types.Message):
    with open("data/Ковалевский Сергей.pdf", "rb") as file:
        await message.answer_document(file, caption="Вот твой PDF с промптами 🚀")

@dp.message_handler(lambda message: message.text == "💳 Купить 50+ промптов")
async def buy_prompts(message: types.Message):
    await message.answer(
        "Для покупки набора из 50+ промптов перейди по ссылке и оформи оплату: \n\nhttps://boosty.to/your-link\n\nПосле оплаты напиши сюда, и я пришлю тебе доступ 🚀"
    )

@dp.message_handler(lambda message: message.text == "✨ Индивидуальные промпты")
async def custom_request(message: types.Message):
    await message.answer(
        "Опиши свою задачу — и я подготовлю персональные промпты специально под тебя. Чем подробнее, тем лучше!"
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
