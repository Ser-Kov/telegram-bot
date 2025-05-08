import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.types import ReplyKeyboardRemove



# Настройки для продакшн
API_TOKEN = os.environ.get("BOT_TOKEN")
if not API_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


# Инициализация бота
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


# --- Кнопки --- #
def get_main_keyboard(after_faq=False):
    kb = ReplyKeyboardBuilder()
    kb.button(text="📎 Скачать беслатный PDF")
    if after_faq:
        kb.button(text="💳 Купить продвинутый PDF (249 ₽)")
    else:
        kb.button(text="📘 Что внутри платного PDF?")
    kb.button(text="✨ Индивидуальные промпты")
    kb.button(text="📄 Публичная оферта")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

def get_return_to_menu_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🏠 Вернуться в меню")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

def after_preview_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📘 Что внутри платного PDF?")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

def get_buy_or_back_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="💳 Купить продвинутый PDF (249 ₽)")
    kb.button(text="🏠 Вернуться в меню")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

def get_payment_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Купить (249 ₽)", url="https://boosty.to/your-link")  # ← замени на свою ссылку
    return kb.as_markup()

# --- Этап 1: FAQ-блок 1 (5 возражений) --- #
faq_stage_1 = {
    "faq_use": "📘 Не переживай! Внутри PDF есть краткая инструкция — ты легко разберёшься, даже если новичок.",
    "faq_price": "📌 Простой вопрос: ты хочешь сэкономить десятки часов и начать зарабатывать с помощью ИИ — или сэкономить 249 ₽?\n\n"
                 "Ты получаешь набор, который заменяет тебе консультанта, сценариста и маркетолога в одном файле.",
    "faq_examples": "<b>💡 Пример промпта:</b>\n"
    "Сгенерируй 5 сценариев для Reels (до 30 сек), которые продвигают [продукт/экспертность] в Instagram.\n\n"
    "Каждый сценарий должен:\n"
    "– начинаться с «крючка» на основе боли клиента: [боль]\n"
    "– содержать одну ключевую мысль, которая ломает шаблон\n"
    "– завершаться лёгким CTA без давления\n"
    "– быть в формате: [селфи / b-roll / voiceover / экран]\n\n"
    "Дополнительно предложи стиль подачи и 1–2 актуальных хештега под каждый сценарий.",
    "faq_bonus": "🎁 Бонус — это чеклист «Как запустить свой продукт с ИИ» — пошаговый мини-план запуска.",
    "faq_later": "⏱ Конечно, можно. Но бонус доступен только сейчас — потом он будет продаваться отдельно."
}

# --- Этап 2: FAQ-блок 2 (4 доп. возражения) --- #
faq_stage_2 = {
    "faq_newbie": "🧩 Ты можешь быть новичком — но промпты сделаны так, чтобы справился любой.",
    "faq_result": "🎯 Уже с первого промпта можно сэкономить 30–60 минут или придумать идею.",
    "faq_risk": "📎 Никаких рисков: ты просто скачиваешь PDF. Без подписок, без навязывания.",
    "faq_value": "📈 Даже 1 идея из 50 может дать тебе результат выше 249 ₽. Это выгодная инвестиция."
}

# --- Генератор клавиатуры из оставшихся ключей --- #
def generate_faq_keyboard(keys_left):
    kb = InlineKeyboardBuilder()
    for key in keys_left:
        label = {
            "faq_use": "🤔 Как это использовать?",
            "faq_price": "💸 Почему это стоит 249 ₽?",
            "faq_examples": "❓ Есть ещё примеры?",
            "faq_bonus": "🎁 Что за бонус?",
            "faq_later": "⏱ А если купить позже?",
            "faq_newbie": "👶 Я новичок — подойдёт?",
            "faq_result": "📊 А результат точно будет?",
            "faq_risk": "🛑 А если не подойдёт?",
            "faq_value": "💡 А в чём ценность?"
        }.get(key, key)
        kb.button(text=label, callback_data=key)
    kb.adjust(1)
    return kb.as_markup()

# --- Временное хранилище для статуса пользователя --- #
faq_state = {}  # {user_id: {"stage": 1, "answered": []}}

# --- Хендлеры --- #
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! 👋\n\nЯ помогу тебе использовать нейросети эффективно. Получи бесплатный PDF с 10 промптами и начни прямо сейчас!",
        reply_markup=get_main_keyboard()
    )

@router.message(lambda msg: msg.text == "🏠 Вернуться в меню")
async def return_to_main(message: Message):
    user_id = message.from_user.id
    is_faq_done = faq_state.get(user_id, {}).get("finished", False)

    await message.answer(
        "Вы вернулись в главное меню:",
        reply_markup=get_main_keyboard(after_faq=is_faq_done)
    )



@router.message(lambda msg: msg.text == "📎 Скачать беслатный PDF")
async def send_pdf(message: Message):
    file = FSInputFile("data/10 промптов для ChatGPT.pdf", filename="10 промптов для ChatGPT.pdf")
    await message.answer_document(
        document=file,
        caption="✅ Вот твой PDF с 10 AI-промптами!"
    )
    await message.answer(
        "📘 Хочешь посмотреть, что внутри расширенного набора на 50+ промптов?\nНажми кнопку ниже 👇",
        reply_markup=after_preview_keyboard()
    )

@router.message(lambda msg: msg.text == "📄 Публичная оферта")
async def send_public_offer(message: Message):
    await message.answer(
        '🧾 <b>Публичная оферта</b> доступна по ссылке:\n\n'
        '<a href="https://telegra.ph/Publichnaya-oferta--AI-Laboratoriya-05-08">Открыть документ</a>',
        parse_mode=ParseMode.HTML
    )

# --- Хендлер: описание платного PDF + старт FAQ-блока --- #
@router.message(lambda msg: msg.text == "📘 Что внутри платного PDF?")
async def show_paid_description(message: Message):
    user_id = message.from_user.id
    faq_state[user_id] = {"stage": 1, "answered": []}

    await message.answer(
        "<b>🎯 Что внутри платного PDF:</b>\n\n"
        "• 50+ продвинутых промптов по темам:\n"
        "📌 Контент | 📌 Продажи | 📌 Бизнес | 📌 Автоматизация\n"
        "📌 Личный бренд | 📌 Делегирование | 📌 WOW-промпты\n\n"
        "• Экономия 10+ часов в неделю\n"
        "• Промпты = мини-команда, которая работает за вас\n"
        "• 🎁 Бонус: Чеклист «Как запустить продукт с ИИ»\n\n"
        "<b>💡 Пример промпта:</b>\n"
        "Придумай упаковку продукта [название], чтобы он воспринимался как «решение №1» для [целевой аудитории].\n\n"
        "Результат должен включать:\n"
        "– мощный оффер (что, для кого, с каким результатом, за сколько)\n"
        "– 3 подзаголовка, раскрывающих ценность\n"
        "– короткий манифест бренда (1 абзац): боль, обещание, доверие\n\n"
        "Ориентируйся на стиль: [эмоционально / прагматично / дерзко]\n"
        "Формат результата: тексты, готовые для лендинга и соцсетей.\n\n"
        "<b>💰 Цена: 249 ₽</b>\n"
        "📎 PDF + бонус внутри, без подписки и лишних шагов",
        parse_mode=ParseMode.HTML
    )

    await message.answer(
        "❓ <b>Остались сомнения?</b> Нажми на вопрос:",
        reply_markup=generate_faq_keyboard(list(faq_stage_1.keys())),
        parse_mode=ParseMode.HTML
    )

    await message.answer(
        "Выберите действие 👇",
        reply_markup=get_buy_or_back_keyboard()
    )

# --- Обработка inline-ответов на возражения --- #
@router.callback_query(lambda c: c.data.startswith("faq_"))
async def handle_faq_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = faq_state.get(user_id)

    if not user_data:
        await callback.answer("Сначала нажми на кнопку 📘 Что внутри платного PDF", show_alert=True)
        return

    stage = user_data["stage"]
    answered = user_data["answered"]

    block = faq_stage_1 if stage == 1 else faq_stage_2
    remaining_keys = [k for k in block.keys() if k not in answered]

    key = callback.data
    if key in answered:
        await callback.answer()
        return

    answered.append(key)
    remaining_keys.remove(key)

    await callback.message.answer(block[key])

    if remaining_keys:
        faq_state[user_id]["answered"] = answered
        await callback.message.answer(
            "🔁 Что ещё может останавливать?",
            reply_markup=generate_faq_keyboard(remaining_keys)
        )
    else:
        if stage == 1:
            faq_state[user_id]["stage"] = 2
            faq_state[user_id]["answered"] = []
            await callback.message.answer(
                "✅ Спасибо за вопросы!\n\n📌 А теперь — ещё несколько важных моментов:",
                reply_markup=generate_faq_keyboard(list(faq_stage_2.keys()))
            )
        else:
            faq_state[user_id]["finished"] = True  # <--- Запоминаем, что пользователь прошёл FAQ
            await callback.message.answer(
                "✅ Все возражения сняты. Пора действовать!\n\n👇 Забери свой продвинутый PDF:",
                reply_markup=get_payment_button()
            )
            await callback.message.answer(
                "⬅️ Или вернуться в меню:",
                reply_markup=get_return_to_menu_keyboard()
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
        "— Хочу автоматизировать работу с Excel и таблицами",
    )


    await message.answer(
        "Чтобы вернуться в главное меню — нажми кнопку ниже 👇",
        reply_markup=get_return_to_menu_keyboard()
    )

@router.message(lambda msg: msg.text == "💳 Купить продвинутый PDF (249 ₽)")
async def handle_payment(message: Message):
    await message.answer(
        "👉 <b>Оплатить и получить PDF:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_payment_button()  # инлайн-ссылка
    )

    await message.answer(
        "⬅️ Или вернуться в меню:",
        reply_markup=get_return_to_menu_keyboard()  # только одна кнопка
    )




# --- Запуск --- #
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
