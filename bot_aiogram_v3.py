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
from aiogram.types import FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery



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
    kb.button(text="📘 Что внутри платного PDF")
    kb.button(text="✨ Индивидуальные промпты")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

# Инлайн клавиатура с возражениями
def get_objections_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤔 А как это использовать?", callback_data="faq_use")],
        [InlineKeyboardButton(text="💸 А точно стоит 249 ₽?", callback_data="faq_price")],
        [InlineKeyboardButton(text="❓ Есть ещё примеры?", callback_data="faq_examples")],
        [InlineKeyboardButton(text="🎁 А что за бонус?", callback_data="faq_bonus")],
        [InlineKeyboardButton(text="⏱ Можно купить позже?", callback_data="faq_later")]
    ])


# --- Хендлеры --- #
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! 👋\n\nЯ помогу тебе использовать нейросети эффективно. Получи бесплатный PDF с 10 промптами и начни прямо сейчас!",
        reply_markup=get_main_keyboard()
    )


@router.message(lambda msg: msg.text == "📄 Скачать PDF")
async def send_pdf(message: Message):
    file = FSInputFile("data/10 промптов для ChatGPT.pdf", filename="10 промптов для ChatGPT.pdf")
    await message.answer_document(
        document=file,
        caption="✅ Вот твой PDF с 10 AI-промптами!\n\n"
                "📘 Хочешь увидеть, что внутри расширенного набора на 50+ промптов? Нажми кнопку ниже — покажу примеры и бонус 🎁"
    )


@router.message(lambda msg: msg.text == "📘 Что внутри платного PDF")
async def show_paid_description(message: Message):
    await message.answer(
        "<b>🎯 Что внутри платного PDF:</b>\n\n"
        "• 50+ продвинутых промптов по темам:\n"
        "📌 Контент | 📌 Продажи | 📌 Бизнес | 📌 Автоматизация\n"
        "📌 Личный бренд | 📌 Делегирование | 📌 WOW-промпты\n\n"
        "• Экономия 10+ часов в неделю\n"
        "• Промпты = мини-команда, которая работает за вас\n"
        "• 🎁 Бонус: Чеклист «Как запустить продукт с ИИ»\n\n"
        "<b>💡 Пример промпта:</b>\n"
        "Придумай 5 офферов для онлайн-курса по [тема], делая акцент на боль клиента: [боль]\n\n"
        "<b>💰 Цена: 249 ₽</b>\n"
        "📎 PDF + бонус внутри, без подписки и лишних шагов",
        parse_mode=ParseMode.HTML,
        reply_markup=get_objections_keyboard()
    )

# Ответы на FAQ
@router.callback_query(lambda c: c.data.startswith("faq_"))
async def handle_faq(callback: CallbackQuery):
    faq = {
        "faq_use": "📘 Не переживай! Внутри PDF есть краткая инструкция — ты легко разберёшься, даже если новичок.",
        "faq_price": "💰 Один хороший промпт экономит час времени. Ты получаешь 50+. Это меньше чашки кофе.",
        "faq_examples": "🧠 Пример:\n«Сгенерируй 10 Reels-сценариев для эксперта по саморазвитию с фокусом на боли подписчиков».",
        "faq_bonus": "🎁 Бонус — это чеклист «Как запустить свой продукт с ИИ» — пошаговый мини-план запуска.",
        "faq_later": "⏳ Конечно, но бонус доступен только сейчас. Потом он будет продаваться отдельно."
    }

    response = faq.get(callback.data, "❓ Неизвестный вопрос.")
    await callback.message.answer(response)

    # Повторно даём ссылку на покупку
    await callback.message.answer(
        "👉 <b>Оплатить и получить PDF:</b> https://boosty.to/your-link\n\n"
        "После оплаты — напиши сюда, и я вышлю тебе файл 📩",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@router.message(lambda msg: msg.text == "✨ Индивидуальные промпты")
async def custom_prompts(message: Message):
    await message.answer(
        "🧠 Опиши свою задачу — и я подготовлю персональные промпты специально под тебя.\n\n"
        "Чем подробнее, тем лучше!\n"
        "Например:\n"
        "— Хочу промпты для контента в Instagram\n"
        "— Нужны идеи для запуска онлайн-курса\n"
        "— Хочу автоматизировать работу с Excel и таблицами"
    )


# --- Запуск --- #
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
