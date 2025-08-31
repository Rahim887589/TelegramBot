import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter

from config import BOT_TOKEN
from handlers.admin import router as admin_router, admin_menu
from admin_storage import load_admins
from faq_mongo import get_all_categories, get_faq_by_category  # функции работы с MongoDB

ADMIN_IDS = load_admins()

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_router(admin_router)


async def get_main_kb(user_id):
    cats = await get_all_categories()
    buttons = [[KeyboardButton(text=cat)] for cat in sorted(cats)]
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="Админ")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    kb = await get_main_kb(message.from_user.id)
    await message.answer("Выберите категорию вопросов:", reply_markup=kb)


@dp.message(F.text.lower() == "админ")
async def admin_button_handler(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("У вас нет прав доступа.")
    await state.clear()
    await admin_menu(message, state)


@dp.message(StateFilter(None))
async def handle_category_or_back(message: Message, state: FSMContext):
    text = message.text
    if text == "⬅️ Назад":
        await state.clear()
        kb = await get_main_kb(message.from_user.id)
        await message.answer("Вы в главном меню.", reply_markup=kb)
        return

    cats = await get_all_categories()
    if text in cats:
        questions = await get_faq_by_category(text)
        if not questions:
            await message.answer("В этой категории пока нет вопросов.")
            return
        await state.set_data({"selected_category": text})

        buttons = [[KeyboardButton(text=q)] for q in sorted(questions.keys())]
        buttons.append([KeyboardButton(text="⬅️ Назад")])
        kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
        await message.answer(f"Вы выбрали категорию <b>{text}</b>. Выберите вопрос:", reply_markup=kb)
        return

    # Если текст не категория, попробуем считать его вопросом
    data = await state.get_data()
    category = data.get("selected_category")
    if category:
        questions = await get_faq_by_category(category)
        if text in questions:
            answer = questions[text]
            await message.answer(f"<b>Вопрос:</b> {text}\n\n<b>Ответ:</b> {answer}")
            return
    # Если ничего не подошло — просим выбрать категорию
    await message.answer("Пожалуйста, выберите категорию из списка или нажмите ⬅️ Назад.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
