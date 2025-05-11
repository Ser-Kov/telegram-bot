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
from fastapi import FastAPI, Request
import hashlib
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import time



# Настройки для продакшн
API_TOKEN = os.environ.get("BOT_TOKEN")
if not API_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


# Инициализация бота
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# --- Переменные --- #
free_pdf_reminders = {
    # user_id: {"start": timestamp, "last_remind": None, "attempts": 0}
}

paid_view_timestamps = {
    # user_id: {"start": timestamp, "last_remind": None, "attempts": 0}
}

FREE_REMINDER_TEXTS = [
    "👋 Ты не забрал бесплатный PDF — он по-прежнему доступен.\n10 шаблонов, чтобы сэкономить часы. Забери пока не забыл:",
    "📌 Напоминаю: твой бесплатный AI-набор ещё ждёт. 10 промптов, чтобы упростить работу и протестировать ИИ в деле.",
    "🔄 Пропустил старт? Бесплатный PDF с промптами всё ещё активен. Забери — и начни применять сегодня:"
]

PAID_REMINDER_TEXTS = [
    "💡 Уже применил бесплатные промпты? Тогда ты готов на следующий шаг.\nВ платных PDF — глубже, точнее и под результат.",
    "📈 Следующий уровень уже рядом — платные PDF помогут выжать максимум из нейросети. Инструкция, шаблоны, чек-лист.",
    "🔥 Пока другие пишут вручную — у тебя есть шанс автоматизировать через ИИ. Забери нужный PDF и внедри уже сегодня."
]


# --- Кнопки --- #
def get_main_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📎 Скачать беслатный PDF")
    kb.button(text="🔥 Что внутри платных PDF?")
    kb.button(text="✨ Индивидуальные промпты")
    kb.button(text="📩 Написать автору")
    kb.button(text="📄 Публичная оферта")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def after_preview_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔥 Что внутри платных PDF?")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


# --- Хендлеры --- #
@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in free_pdf_reminders:
        free_pdf_reminders[user_id] = {
            "start": time.time(),
            "last_remind": None,
            "attempts": 0
        }
    await message.answer(
        "Привет! 👋\n\nЯ помогу тебе использовать нейросети эффективно. Получи бесплатный PDF "
        "с 10 промптами и начни прямо сейчас!",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("menu"))
async def show_menu(message: Message):
    await message.answer(
        "🏠 <b>Главное меню</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )


@router.message(lambda msg: msg.text == "📎 Скачать беслатный PDF")
async def send_pdf(message: Message):
    file = FSInputFile("data/10 промптов для ChatGPT.pdf", filename="10 промптов для ChatGPT.pdf")
    await message.answer_document(
        document=file,
        caption="✅ Вот твой PDF с 10 AI-промптами — стартовый набор, чтобы попробовать в деле."
    )
    await message.answer(
        "🚀 Хочешь перейти на продвинутый уровень?\n\n"
        "У нас есть 7 PDF по конкретным нишам: маркетинг, Reels, блогеры, курсы, офлайн и т.д.\n\n"
        "Нажми 👉 <b>🔥 Что внутри платных PDF?</b>",
        reply_markup=after_preview_keyboard()
    )
    user_id = message.from_user.id
    if user_id in free_pdf_reminders:
        del free_pdf_reminders[user_id]



@router.message(lambda msg: msg.text == "📄 Публичная оферта")
async def send_public_offer(message: Message):
    await message.answer(
        '🧾 <b>Публичная оферта</b> доступна по ссылке:\n\n'
        '<a href="https://telegra.ph/Publichnaya-oferta--AI-Laboratoriya-05-08">Открыть документ</a>',
        parse_mode=ParseMode.HTML,
        reply_markup=types.ReplyKeyboardRemove()
    )


@router.message(lambda msg: msg.text == "✨ Индивидуальные промпты")
async def start_custom_prompt(message: Message, state: FSMContext):
    await state.set_state(CustomPromptForm.waiting_for_description)
    await message.answer(
        "🧠 <b>Опиши как можно подробнее, какая задача перед тобой стоит:</b>\n\n"
        "— Где ты планируешь применять промпты? (Instagram, сайт, продажи, реклама, обучение...)\n"
        "— Что именно хочешь получить в результате? (идеи, структура, тексты, формулировки...)\n"
        "— Какая у тебя ниша / продукт / аудитория?\n\n"
        "✍️ <b>Пример:</b>\n"
        "«Я продвигаю онлайн-курс для экспертов. Хочу серию сторис и Reels, которые вовлекают и ведут к "
        "покупке. ЦА — психологи и коучи. Канал — Instagram.»\n\n"
        "📌 Чем подробнее — тем качественнее будут промпты. Напиши ниже 👇",
        parse_mode=ParseMode.HTML,
        reply_markup=types.ReplyKeyboardRemove()
    )
    

@router.callback_query(lambda c: c.data == "custom_prompt")
async def handle_custom_prompt_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🧠 <b>Опиши как можно подробнее, какая задача перед тобой стоит:</b>\n\n"
        "— Где ты планируешь применять промпты? (Instagram, сайт, продажи, реклама, обучение...)\n"
        "— Что именно хочешь получить в результате? (идеи, структура, тексты, формулировки...)\n"
        "— Какая у тебя ниша / продукт / аудитория?\n\n"
        "✍️ <b>Пример:</b>\n"
        "«Я продвигаю онлайн-курс для экспертов. Хочу серию сторис и Reels, которые вовлекают и ведут к покупке. "
        "ЦА — психологи и коучи. Канал — Instagram.»\n\n"
        "📌 Чем подробнее — тем качественнее будут промпты. Напиши ниже 👇",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(CustomPromptForm.waiting_for_description)
    await callback.answer()


# --- Хендлер: описание платного PDF --- #
@router.message(lambda msg: msg.text == "🔥 Что внутри платных PDF?")
async def show_paid_options(message: Message):
    # Клавиатура с нишами
    kb = InlineKeyboardBuilder()
    kb.button(text="📹 Reels", callback_data="niche_reels")
    kb.button(text="📱 SMM", callback_data="niche_smm")
    kb.button(text="👤 Блогеры", callback_data="niche_blog")
    kb.button(text="🏪 Офлайн-бизнес", callback_data="niche_offline")
    kb.button(text="🎓 Онлайн-курсы", callback_data="niche_courses")
    kb.button(text="📦 Товарка", callback_data="niche_ecom")
    kb.button(text="💼 Фриланс", callback_data="niche_freelance")
    kb.adjust(2)

    user_id = message.from_user.id
    if user_id not in paid_view_timestamps:
        paid_view_timestamps[user_id] = {
            "start": time.time(),
            "last_remind": None,
            "attempts": 0
        }

    await message.answer(
        "👇 Выбери интересующую нишу, чтобы раскрыть содержимое PDF и получить ссылку на покупку:",
        reply_markup=kb.as_markup()
    )

    # Отдельное сообщение про Индивидуальные промпты
    ind_kb = InlineKeyboardBuilder()
    ind_kb.button(text="✨ Индивидуальные промпты", callback_data="custom_prompt")
    await message.answer(
        "❓ Не нашёл свою нишу?\nПопробуй <b>Индивидуальные промпты</b> — мы соберём PDF под твою задачу:",
        parse_mode=ParseMode.HTML,
        reply_markup=ind_kb.as_markup()
    )
    
    await message.answer(
    "👇 Для возврата в главное меню",
    reply_markup=types.ReplyKeyboardRemove()
    )


@router.callback_query(lambda c: c.data.startswith("niche_"))
async def show_niche_pdf(callback: CallbackQuery):
    niche = callback.data.replace("niche_", "")
    descriptions = {
        "reels": (
            "🎬 <b>Reels-промпты для Instagram и TikTok</b>\n\n"
            "⚡ Хватит снимать наобум! Этот PDF даёт:\n"
            "• 5 вирусных сценариев под Reels + крючки, хештеги и структура видео\n"
            "• Примеры форматов: voiceover, экран, селфи\n"
            "• Стили подачи: от экспертного до дерзкого\n\n"
            "🧩 Ты получишь 5 продвинутых промптов, каждый из которых проработан под ключевые сценарии ниши.\n"
            "Они точнее, глубже и практичнее, чем в бесплатном PDF — потому что созданы для конкретного результата.\n\n"
            "💬 Частые сомнения:\n"
            "– «Уже снимал, не заходит» → Промпты обновлены под алгоритмы 2025\n"
            "– «Не знаю, что сказать в кадре» → Просто следуй шаблону: 1 минута — и видео готово\n\n"
            "🎯 Уже через 10 минут у тебя будет 5 готовых сценариев, которые можно снимать сегодня\n"
            "❗ Или снова потратишь вечер, листая Reels конкурентов без плана\n"
            "💳 PDF за 249 ₽ — и ты снимаешь уверенно, без ступора\n\n"
            "🔍 <b>Что внутри PDF:</b>\n"
            "• 5 продвинутых промптов под ключевые задачи в нише\n"
            "• Пошаговая инструкция по применению (куда вставлять, что адаптировать)\n"
            "• 🎁 Бонус: чек-лист «<i>Как оформить Reels, чтобы увеличить досмотры и сохранения</i>» — чтобы внедрить результат быстрее"
        ),

        "smm": (
            "📱 <b>Промпты для SMM-специалистов и контент-маркетинга</b>\n\n"
            "📌 Сформируй мощный контент-план за час:\n"
            "• Промпты для лид-магнитов, прогревов, акций\n"
            "• Идеи вовлекающих постов и Reels\n"
            "• Примеры заголовков и сторителлинга\n\n"
            "🧩 Ты получишь 5 продвинутых промптов, каждый из которых проработан под ключевые сценарии ниши.\n"
            "Они точнее, глубже и практичнее, чем в бесплатном PDF — потому что созданы для конкретного результата.\n\n"
            "💬 Частые возражения:\n"
            "– «У клиентов разная ниша» → Промпты универсальны и адаптируются под любую тему\n"
            "– «Я уже работаю с ИИ» → Но ты не видел таких инструкций: они продвигают, а не просто пишут\n\n"
            "🎯 Уже сегодня ты сможешь набросать план контента на неделю вперёд\n"
            "❗ Или продолжишь вымучивать посты по одной идее в день\n"
            "💳 PDF за 249 ₽ — ассистент для контентщика, который не ноет и не устает\n\n"
            "🔍 <b>Что внутри PDF:</b>\n"
            "• 5 продвинутых промптов под ключевые задачи в нише\n"
            "• Пошаговая инструкция по применению (куда вставлять, что адаптировать)\n"
            "• 🎁 Бонус: чек-лист «<i>Контент, который сохраняют, комментируют и ждут</i>» — чтобы внедрить результат быстрее"
        ),

        "blog": (
            "👤 <b>Промпты для блогеров и личного бренда</b>\n\n"
            "🎯 Сделай контент сильным, искренним и цепляющим:\n"
            "• Промпты для раскрытия экспертности и эмоций\n"
            "• Шаблоны прогревов, рубрик и сторис\n"
            "• Структуры вовлекающего повествования\n\n"
            "🧩 Ты получишь 5 продвинутых промптов, каждый из которых проработан под ключевые сценарии ниши.\n"
            "Они точнее, глубже и практичнее, чем в бесплатном PDF — потому что созданы для конкретного результата.\n\n"
            "💬 Сомнения:\n"
            "– «Я не умею красиво писать» → Просто вставь свои мысли в шаблон — получится огонь\n"
            "– «Моя тема не заходит» → Бренд продаёт через доверие, а не через тему. Эти промпты строят доверие\n\n"
            "🎯 У тебя будет запас постов и сторис с сильным посылом уже сегодня\n"
            "❗ Или опять откроешь Instagram — и закроешь, не зная, что писать\n"
            "💳 PDF за 249 ₽ — твой контент-продюсер в одном файле\n\n"
            "🔍 <b>Что внутри PDF:</b>\n"
            "• 5 продвинутых промптов под ключевые задачи в нише\n"
            "• Пошаговая инструкция по применению (куда вставлять, что адаптировать)\n"
            "• 🎁 Бонус: чек-лист «<i>Что делает личный бренд магнитом для клиентов</i>» — чтобы внедрить результат быстрее"
        ),

        "offline": (
            "🏪 <b>Промпты для малого офлайн-бизнеса</b>\n\n"
            "📦 Магазин, салон, студия — сделай так, чтобы клиенты хотели прийти:\n"
            "• Готовые тексты для постов, листовок и мессенджеров\n"
            "• Идеи сторис, акций и коротких роликов\n"
            "• Промпты для объяснения пользы и выгоды\n\n"
            "🧩 Ты получишь 5 продвинутых промптов, каждый из которых проработан под ключевые сценарии ниши.\n"
            "Они точнее, глубже и практичнее, чем в бесплатном PDF — потому что созданы для конкретного результата.\n\n"
            "💬 Частые сомнения:\n"
            "– «А у меня локальный бизнес» → Именно поэтому тебе нужен сильный посыл в онлайне\n"
            "– «Я не копирайтер» → И не надо. Просто используй шаблон и вставь название своего бизнеса\n\n"
            "🎯 Уже сегодня сможешь оформить пост, объявление и рассылку без головной боли\n"
            "❗ Или оставишь страницу пустой — и клиенты пойдут к конкуренту\n"
            "💳 PDF за 249 ₽ — как нанять маркетолога на 1 день за копейки\n\n"
            "🔍 <b>Что внутри PDF:</b>\n"
            "• 5 продвинутых промптов под ключевые задачи в нише\n"
            "• Пошаговая инструкция по применению (куда вставлять, что адаптировать)\n"
            "• 🎁 Бонус: чек-лист «<i>Как продавать через личный стиль, даже если у тебя офлайн-бизнес</i>» — чтобы внедрить результат быстрее"
        ),

        "courses": (
            "🎓 <b>Промпты для онлайн-курсов и инфобизнеса</b>\n\n"
            "🚀 Запуск на автопилоте:\n"
            "• Промпты для структуры курса, уроков, вебинара, лендинга\n"
            "• Идеи для «прогрева» и сторителлинга\n"
            "• Генерация офферов и лид-магнитов\n\n"
            "🧩 Ты получишь 5 продвинутых промптов, каждый из которых проработан под ключевые сценарии ниши.\n"
            "Они точнее, глубже и практичнее, чем в бесплатном PDF — потому что созданы для конкретного результата.\n\n"
            "💬 Сомнения:\n"
            "– «Я только собираюсь запускаться» → Значит, начни правильно — с чёткой структуры и оффера\n"
            "– «Я уже продаю» → Тогда сократи время и усилия на контент в 5 раз\n\n"
            "🎯 Через 15 минут у тебя будет каркас курса и продающий текст\n"
            "❗ Или будешь снова писать всё «с нуля» каждый запуск\n"
            "💳 PDF за 249 ₽ — без методиста, без копирайтера, без задержек\n\n"
            "🔍 <b>Что внутри PDF:</b>\n"
            "• 5 продвинутых промптов под ключевые задачи в нише\n"
            "• Пошаговая инструкция по применению (куда вставлять, что адаптировать)\n"
            "• 🎁 Бонус: чек-лист «<i>Что должно быть в продающем посте, Reels или эфире</i>» — чтобы внедрить результат быстрее"
        ),

        "ecom": (
            "📦 <b>Промпты для товарки и интернет-магазинов</b>\n\n"
            "🛍 Продавай словами, которые цепляют:\n"
            "• Упаковка карточек: офферы, преимущества, УТП\n"
            "• Промпты для отзывов, сторис, рекламы\n"
            "• Автоматизация шаблонов в переписке\n\n"
            "🧩 Ты получишь 5 продвинутых промптов, каждый из которых проработан под ключевые сценарии ниши.\n"
            "Они точнее, глубже и практичнее, чем в бесплатном PDF — потому что созданы для конкретного результата.\n\n"
            "💬 Возражения:\n"
            "– «Мой товар не отличается от других» → Слова решают. Эти промпты превращают обычный товар в «надо срочно»\n"
            "– «Нет времени» → Готовый файл = 15 минут — и продающий контент готов\n\n"
            "🎯 Уже сегодня ты сможешь переупаковать карточку товара и тексты\n"
            "❗ Или будешь снова снижать цену и ждать отклика\n"
            "💳 PDF за 249 ₽ — твой скрытый продавец на всех площадках\n\n"
            "🔍 <b>Что внутри PDF:</b>\n"
            "• 5 продвинутых промптов под ключевые задачи в нише\n"
            "• Пошаговая инструкция по применению (куда вставлять, что адаптировать)\n"
            "• 🎁 Бонус: чек-лист «<i>Как сделать товар визуально желанным и кликабельным</i>» — чтобы внедрить результат быстрее"
        ),

        "freelance": (
            "💼 <b>Промпты для фрилансеров и специалистов услуг</b>\n\n"
            "🧠 Упакуй свои услуги и увеличь доход:\n"
            "• Промпты для описания профиля и портфолио\n"
            "• Сценарии первых сообщений клиенту\n"
            "• Шаблоны прогрева и объяснения ценности\n\n"
            "🧩 Ты получишь 5 продвинутых промптов, каждый из которых проработан под ключевые сценарии ниши.\n"
            "Они точнее, глубже и практичнее, чем в бесплатном PDF — потому что созданы для конкретного результата.\n\n"
            "💬 Возражения:\n"
            "– «Услуги сложно объяснить» → Эти промпты переводят экспертность в простую выгоду для клиента\n"
            "– «Мало заказов» → Ты либо не доносишь ценность, либо не цепляешь — PDF исправит это\n\n"
            "🎯 Уже сегодня ты сможешь переписать профиль, заявку и начать зарабатывать больше\n"
            "❗ Или останешься среди тех, кто пишет «делаю быстро и недорого» — и сидит без заказов\n"
            "💳 PDF за 249 ₽ — как упаковка на миллион без дизайна\n\n"
            "🔍 <b>Что внутри PDF:</b>\n"
            "• 5 продвинутых промптов под ключевые задачи в нише\n"
            "• Пошаговая инструкция по применению (куда вставлять, что адаптировать)\n"
            "• 🎁 Бонус: чек-лист «<i>Как преподнести свою услугу, чтобы платили дороже</i>» — чтобы внедрить результат быстрее"
        ),
    }

    text = descriptions.get(niche, "Информация по этой нише будет добавлена позже.")
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Оплатить 249 ₽", url="https://example.com/payment_placeholder")
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb.as_markup())
    await callback.answer()

custom_requests = {}  # user_id: {"text": str, "timestamp": float}


class CustomPromptForm(StatesGroup):
    waiting_for_description = State()


async def clear_request_after_timeout(user_id: int, delay: int = 1800):
    await asyncio.sleep(delay)
    if user_id in custom_requests:
        del custom_requests[user_id]


@router.message(CustomPromptForm.waiting_for_description)
async def receive_description(message: Message, state: FSMContext):
    user_id = message.from_user.id
    description = message.text.strip()

    # Сохраняем заявку
    custom_requests[user_id] = {
        "text": description,
        "timestamp": time.time()
    }

    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Оплатить 499 ₽", url="https://example.com/custom_payment_placeholder")

    await message.answer(
    "✅ <b>Заявка получена!</b>\n\n"
    "Мы подготовим <b>3 индивидуальных AI-промпта</b> под твою задачу: по структуре, тону, платформе и результату.\n\n"
    "💳 Стоимость — <b>499 ₽</b>\n"
    "⏳ Важно: ссылка на оплату будет действительна <b>30 минут</b>.\n\n"
    "После оплаты заявка поступит в работу, и ты получишь PDF напрямую в Telegram.",
    parse_mode=ParseMode.HTML,
    reply_markup=kb.as_markup()
    )


    await state.clear()

    # Запускаем автоудаление заявки через 30 минут
    asyncio.create_task(clear_request_after_timeout(user_id, delay=1800))


@router.message(lambda msg: msg.text == "📩 Написать автору")
async def contact_author(message: Message):
    await message.answer(
        "📩 <b>Связаться с автором проекта</b>\n\n"
        "Если у тебя остались вопросы, что-то не сработало или нужна помощь — ты можешь напрямую написать автору проекта.\n\n"
        "<b>Сергей Ковалевский</b> — создатель этого бота и всех PDF, отвечает лично. Просьба уважительно формулировать сообщение и сразу писать по делу 🙏\n\n"
        "🔗 <a href=\"https://t.me/ser_kovalevsky\">Написать Сергею Ковалевскому</a>\n",
        parse_mode=ParseMode.HTML,
        reply_markup=types.ReplyKeyboardRemove()
    )


# Robokassa настройки
ROBO_LOGIN = "ai_lab"
ROBO_PASSWORD2 = "sKNbUPuD24G7P0oadt3A"

# Таблица соответствий кодов товара и PDF
PRODUCTS = {
    "reels": "data/Продвинутые Reels-промпты для Instagram и TikTok.pdf",
    "smm": "data/Продвинутые промпты для SMM-специалистов и контент-маркетинга.pdf",
    "blog": "data/Продвинутые промпты для блогеров и личного бренда.pdf",
    "offline": "data/Продвинутые промпты для малого бизнеса и офлайн-услуг.pdf",
    "courses": "data/Продвинутые промпты для онлайн-курсов и инфобизнеса.pdf",
    "ecom": "data/Продвинутые промпты для товарного бизнеса и интернет-магазинов.pdf",
    "freelance": "data/Продвинутые промпты для фрилансеров и специалистов услуг.pdf"
}

# --- FastAPI для Robokassa --- #
app = FastAPI()


@app.post("/payment_callback")
async def robokassa_payment_handler(request: Request):
    form = await request.form()
    OutSum = form.get("OutSum")
    InvId = form.get("InvId")
    SignatureValue = form.get("SignatureValue")

    # Только боевая проверка
    base = f"{OutSum}:{InvId}:{ROBO_PASSWORD2}"
    expected_signature = hashlib.md5(base.encode()).hexdigest().upper()

    if SignatureValue.upper() != expected_signature:
        return "bad sign"

    try:
        tg_user_id, product_code = InvId.split("_")
        pdf_path = PRODUCTS.get(product_code)
        if not pdf_path:
            return "product not found"

        file = FSInputFile(pdf_path)
        await bot.send_document(chat_id=int(tg_user_id), document=file,
                                caption="✅ Спасибо за оплату! Вот ваш PDF.")
        return "OK"
    except Exception as e:
        return f"error: {e}"


async def reminder_loop():
    while True:
        now = time.time()

        # Напоминания о бесплатном PDF
        for user_id, data in list(free_pdf_reminders.items()):
            start = data["start"]
            last_remind = data.get("last_remind")
            attempts = data.get("attempts", 0)

            if now - start >= 40 * 60 and (not last_remind or now - last_remind >= 2 * 3600):
                try:
                    text = FREE_REMINDER_TEXTS[min(attempts, len(FREE_REMINDER_TEXTS) - 1)]
                    await bot.send_message(
                        chat_id=user_id,
                        text=text,
                        reply_markup=get_main_keyboard()
                    )
                    free_pdf_reminders[user_id]["last_remind"] = now
                    free_pdf_reminders[user_id]["attempts"] = attempts + 1
                    if free_pdf_reminders[user_id]["attempts"] >= 3:
                        del free_pdf_reminders[user_id]
                except Exception as e:
                    logging.warning(f"[FREE REMINDER] Ошибка для {user_id}: {e}")

        # Напоминания о платных PDF
        for user_id, data in list(paid_view_timestamps.items()):
            start = data["start"]
            last_remind = data.get("last_remind")
            attempts = data.get("attempts", 0)

            if now - start >= 8 * 3600 and (not last_remind or now - last_remind >= 24 * 3600):
                try:
                    text = PAID_REMINDER_TEXTS[min(attempts, len(PAID_REMINDER_TEXTS) - 1)]
                    await bot.send_message(
                        chat_id=user_id,
                        text=text,
                        reply_markup=types.ReplyKeyboardMarkup(
                            keyboard=[[types.KeyboardButton(text="🔥 Что внутри платных PDF?")]],
                            resize_keyboard=True
                        )
                    )
                    paid_view_timestamps[user_id]["last_remind"] = now
                    paid_view_timestamps[user_id]["attempts"] = attempts + 1
                    if paid_view_timestamps[user_id]["attempts"] >= 3:
                        del paid_view_timestamps[user_id]
                except Exception as e:
                    logging.warning(f"[PAID REMINDER] Ошибка для {user_id}: {e}")

        await asyncio.sleep(300)


# --- Запуск aiogram-бота --- #
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)


@app.on_event("startup")
async def start_bot():
    asyncio.create_task(main())
    asyncio.create_task(reminder_loop())
