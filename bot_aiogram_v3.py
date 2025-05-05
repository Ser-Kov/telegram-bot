import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from aiogram.filters import Command

# Настройки
API_TOKEN = os.environ.get("BOT_TOKEN")
if not API_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

# Инициализация бота
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


# --- Кнопки --- #
def get_main_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📄 Скачать PDF")
    kb.button(text="💳 Купить 50+ промптов")
    kb.button(text="✨ Индивидуальные промпты")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


# --- Хендлеры --- #
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! 👋\n\nЯ помогу тебе использовать нейросети эффективно. Получи бесплатный PDF с 10 промптами и начни прямо сейчас!",
        reply_markup=get_main_keyboard()
    )

@router.message(lambda msg: msg.text == "📄 Скачать PDF")
async def send_pdf(message: Message):
    with open("data/Ковалевский Сергей.pdf", "rb") as file:
        await message.answer_document(file, caption="Вот твой PDF с промптами 🚀")

@router.message(lambda msg: msg.text == "💳 Купить 50+ промптов")
async def buy_prompts(message: Message):
    await message.answer(
        "Для покупки набора из 50+ промптов перейди по ссылке и оформи оплату: \n\nhttps://boosty.to/your-link\n\nПосле оплаты напиши сюда, и я пришлю тебе доступ 🚀"
    )

@router.message(lambda msg: msg.text == "✨ Индивидуальные промпты")
async def custom_prompts(message: Message):
    await message.answer(
        "Опиши свою задачу — и я подготовлю персональные промпты специально под тебя. Чем подробнее, тем лучше!"
    )


# --- Запуск --- #
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
