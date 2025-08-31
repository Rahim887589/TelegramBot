from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from admin_storage import load_admins, save_admins  # файл для списка админов

from faq_mongo import (
    get_all_faq, get_all_categories, get_faq_by_category,
    add_category, rename_category, delete_category,
    add_question, edit_answer, delete_question
)

router = Router()
ADMIN_IDS = load_admins()

# === Состояния ===
class AdminMenu(StatesGroup):
    menu = State()
    add_submenu = State()
    edit_submenu = State()
    delete_submenu = State()
    admin_management = State()

class AddCategory(StatesGroup):
    waiting_name = State()

class AddFAQ(StatesGroup):
    waiting_category = State()
    waiting_question = State()
    waiting_answer = State()

class EditCategory(StatesGroup):
    waiting_category = State()
    waiting_new_name = State()

class EditFAQ(StatesGroup):
    waiting_category = State()
    waiting_question = State()
    waiting_new_answer = State()

class EditQuestion(StatesGroup):
    waiting_category = State()
    waiting_old_question = State()
    waiting_new_question = State()

class DeleteCategory(StatesGroup):
    waiting_confirm = State()
    waiting_category = State()

class DeleteFAQ(StatesGroup):
    waiting_category = State()
    waiting_question = State()
    waiting_confirm = State()

class AdminManagement(StatesGroup):
    menu = State()
    add_admin = State()
    delete_admin = State()

# === Клавиатуры ===
def get_admin_main_menu_kb():
    buttons = [
        [KeyboardButton(text="➕ Добавить")],
        [KeyboardButton(text="✏️ Редактировать")],
        [KeyboardButton(text="🗑 Удалить")],
        [KeyboardButton(text="👑 Управление админами")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_add_submenu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Категория")],
            [KeyboardButton(text="➕ Вопрос")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def get_edit_submenu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Категория")],
            [KeyboardButton(text="✏️ Вопрос")],
            [KeyboardButton(text="✏️ Ответ")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def get_delete_submenu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗑 Категория")],
            [KeyboardButton(text="🗑 Вопрос")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def get_admin_management_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить админа")],
            [KeyboardButton(text="🗑 Удалить админа")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

async def get_categories_kb(back_button=True):
    cats = await get_all_categories()
    buttons = [[KeyboardButton(text=cat)] for cat in sorted(cats)]
    if back_button:
        buttons.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

async def get_questions_kb(category, back_button=True):
    questions = await get_faq_by_category(category)
    buttons = [[KeyboardButton(text=q)] for q in sorted(questions.keys())]
    if back_button:
        buttons.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_confirm_delete_kb():
    buttons = [
        [InlineKeyboardButton(text="✅ Да", callback_data="confirm_delete_yes"),
         InlineKeyboardButton(text="❌ Нет", callback_data="confirm_delete_no")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# === Хендлеры ===

@router.message(Command("admin"))
async def admin_menu(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("🚫 Доступ запрещен")

    faq = await get_all_faq()
    text = "📋 <b>Админ-панель</b>\n\n"
    if not faq:
        text += "Категории не созданы"
    else:
        text += "Список категорий:\n"
        for cat in sorted(faq.keys()):
            q_count = len(faq[cat])
            text += f"• {cat} ({q_count} вопросов)\n"

    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_menu_kb())
    await state.set_state(AdminMenu.menu)

# --- Главное меню ---

@router.message(AdminMenu.menu, F.text == "➕ Добавить")
async def menu_add(message: types.Message, state: FSMContext):
    await message.answer("Выберите, что добавить:", reply_markup=get_add_submenu_kb())
    await state.set_state(AdminMenu.add_submenu)

@router.message(AdminMenu.menu, F.text == "✏️ Редактировать")
async def menu_edit(message: types.Message, state: FSMContext):
    await message.answer("Выберите, что редактировать:", reply_markup=get_edit_submenu_kb())
    await state.set_state(AdminMenu.edit_submenu)

@router.message(AdminMenu.menu, F.text == "🗑 Удалить")
async def menu_delete(message: types.Message, state: FSMContext):
    await message.answer("Выберите, что удалить:", reply_markup=get_delete_submenu_kb())
    await state.set_state(AdminMenu.delete_submenu)

@router.message(AdminMenu.menu, F.text == "👑 Управление админами")
async def menu_admin_management(message: types.Message, state: FSMContext):
    await message.answer("Меню управления админами:", reply_markup=get_admin_management_kb())
    await state.set_state(AdminMenu.admin_management)

@router.message(AdminMenu.menu, F.text == "⬅️ Назад")
async def menu_back(message: types.Message, state: FSMContext):
    await message.answer("Выход из админки.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

# --- Добавление категории ---
@router.message(AdminMenu.add_submenu, F.text == "➕ Категория")
async def add_category_start(message: types.Message, state: FSMContext):
    await message.answer("📝 Введите название категории:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddCategory.waiting_name)

@router.message(AddCategory.waiting_name)
async def add_category_process(message: types.Message, state: FSMContext):
    category = message.text.strip()
    if not category:
        await message.answer("❌ Название не может быть пустым")
        return
    success = await add_category(category)
    if not success:
        await message.answer("❌ Категория уже существует")
        return
    await message.answer(f"✅ Категория '{category}' создана", reply_markup=get_admin_main_menu_kb())
    await state.set_state(AdminMenu.menu)

# --- Добавление вопроса ---
@router.message(AdminMenu.add_submenu, F.text == "➕ Вопрос")
async def add_faq_start(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if not cats:
        await message.answer("❌ Сначала создайте категорию", reply_markup=get_add_submenu_kb())
        return
    await message.answer("Выберите категорию:", reply_markup=await get_categories_kb())
    await state.set_state(AddFAQ.waiting_category)

@router.message(AddFAQ.waiting_category)
async def add_faq_category(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if message.text not in cats:
        await message.answer("❌ Выберите категорию из списка.")
        return
    await state.update_data(category=message.text)
    await message.answer("✏️ Введите вопрос:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddFAQ.waiting_question)

@router.message(AddFAQ.waiting_question)
async def add_faq_question(message: types.Message, state: FSMContext):
    question = message.text.strip()
    if not question:
        await message.answer("❌ Вопрос не может быть пустым")
        return
    data = await state.get_data()
    category = data["category"]
    questions = await get_faq_by_category(category)
    if question in questions:
        await message.answer("❌ Вопрос уже существует в этой категории")
        return
    await state.update_data(question=question)
    await message.answer("📝 Введите ответ:")
    await state.set_state(AddFAQ.waiting_answer)

@router.message(AddFAQ.waiting_answer)
async def add_faq_answer(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    if not answer:
        await message.answer("❌ Ответ не может быть пустым")
        return
    data = await state.get_data()
    category = data["category"]
    question = data["question"]
    success = await add_question(category, question, answer)
    if not success:
        await message.answer("❌ Ошибка при добавлении вопроса.")
        return
    await message.answer(
        f"✅ Добавлено в '{category}':\n\n<b>{question}</b>\n{answer}",
        parse_mode="HTML",
        reply_markup=get_admin_main_menu_kb()
    )
    await state.set_state(AdminMenu.menu)

# --- Редактирование категории ---
@router.message(AdminMenu.edit_submenu, F.text == "✏️ Категория")
async def edit_category_start(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if not cats:
        await message.answer("❌ Категории отсутствуют", reply_markup=get_admin_main_menu_kb())
        await state.set_state(AdminMenu.menu)
        return
    await message.answer("Выберите категорию для редактирования:", reply_markup=await get_categories_kb())
    await state.set_state(EditCategory.waiting_category)

@router.message(EditCategory.waiting_category)
async def edit_category_name(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if message.text not in cats:
        await message.answer("❌ Выберите категорию из списка.")
        return
    await state.update_data(category=message.text)
    await message.answer("Введите новое название категории:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(EditCategory.waiting_new_name)

@router.message(EditCategory.waiting_new_name)
async def edit_category_name_process(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    if not new_name:
        await message.answer("❌ Название не может быть пустым")
        return
    data = await state.get_data()
    old_name = data["category"]
    success = await rename_category(old_name, new_name)
    if not success:
        await message.answer("❌ Ошибка. Возможно, категория с таким именем уже существует.")
        return
    await message.answer(f"✅ Категория '{old_name}' переименована в '{new_name}'", reply_markup=get_admin_main_menu_kb())
    await state.set_state(AdminMenu.menu)

# --- Редактирование вопроса ---
@router.message(AdminMenu.edit_submenu, F.text == "✏️ Вопрос")
async def edit_question_start(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if not cats:
        await message.answer("❌ Категории отсутствуют", reply_markup=get_admin_main_menu_kb())
        await state.set_state(AdminMenu.menu)
        return
    await message.answer("Выберите категорию:", reply_markup=await get_categories_kb())
    await state.set_state(EditQuestion.waiting_category)

@router.message(EditQuestion.waiting_category)
async def edit_question_category(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if message.text not in cats:
        await message.answer("❌ Выберите категорию из списка.")
        return
    await state.update_data(category=message.text)
    await message.answer("Выберите вопрос для редактирования:", reply_markup=await get_questions_kb(message.text))
    await state.set_state(EditQuestion.waiting_old_question)

@router.message(EditQuestion.waiting_old_question)
async def edit_question_old(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data["category"]
    questions = await get_faq_by_category(category)
    if message.text not in questions:
        await message.answer("❌ Вопрос не найден. Выберите из списка.")
        return
    await state.update_data(old_question=message.text)
    await message.answer("Введите новое название вопроса:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(EditQuestion.waiting_new_question)

@router.message(EditQuestion.waiting_new_question)
async def edit_question_new(message: types.Message, state: FSMContext):
    new_q = message.text.strip()
    if not new_q:
        await message.answer("❌ Вопрос не может быть пустым")
        return
    data = await state.get_data()
    category = data["category"]
    old_question = data["old_question"]
    # получаем ответ
    faq = await get_faq_by_category(category)
    if new_q in faq:
        await message.answer("❌ Вопрос с таким названием уже существует.")
        return
    answer = faq.get(old_question)
    # удаляем старый и добавляем новый
    await delete_question(category, old_question)
    await add_question(category, new_q, answer)

    await message.answer(
        f"✅ Вопрос изменён:\n\n<b>{old_question}</b> ➡️ <b>{new_q}</b>",
        parse_mode="HTML",
        reply_markup=get_admin_main_menu_kb()
    )
    await state.set_state(AdminMenu.menu)

# --- Редактирование ответа ---
@router.message(AdminMenu.edit_submenu, F.text == "✏️ Ответ")
async def edit_faq_start(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if not cats:
        await message.answer("❌ Категории отсутствуют", reply_markup=get_admin_main_menu_kb())
        await state.set_state(AdminMenu.menu)
        return
    await message.answer("Выберите категорию:", reply_markup=await get_categories_kb())
    await state.set_state(EditFAQ.waiting_category)

@router.message(EditFAQ.waiting_category)
async def edit_faq_category(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if message.text not in cats:
        await message.answer("❌ Выберите категорию из списка.")
        return
    await state.update_data(category=message.text)
    await message.answer("Выберите вопрос для редактирования ответа:", reply_markup=await get_questions_kb(message.text))
    await state.set_state(EditFAQ.waiting_question)

@router.message(EditFAQ.waiting_question)
async def edit_faq_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    questions = await get_faq_by_category(category)
    if message.text not in questions:
        await message.answer("❌ Вопрос не найден. Выберите из списка.")
        return
    await state.update_data(question=message.text)
    await message.answer("✏️ Введите новый ответ:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(EditFAQ.waiting_new_answer)

@router.message(EditFAQ.waiting_new_answer)
async def edit_faq_answer_process(message: types.Message, state: FSMContext):
    new_answer = message.text.strip()
    if not new_answer:
        await message.answer("❌ Ответ не может быть пустым")
        return
    data = await state.get_data()
    category = data["category"]
    question = data["question"]
    success = await edit_answer(category, question, new_answer)
    if not success:
        await message.answer("❌ Ошибка при обновлении ответа.")
        return
    await message.answer(
        f"✅ Ответ обновлён для:\n\n<b>{question}</b>\n\n<b>Новый ответ:</b>\n{new_answer}",
        parse_mode="HTML",
        reply_markup=get_admin_main_menu_kb()
    )
    await state.set_state(AdminMenu.menu)

# --- Удаление категории ---
@router.message(AdminMenu.delete_submenu, F.text == "🗑 Категория")
async def delete_category_start(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if not cats:
        await message.answer("❌ Категории отсутствуют", reply_markup=get_admin_main_menu_kb())
        await state.set_state(AdminMenu.menu)
        return
    await message.answer("Выберите категорию для удаления:", reply_markup=await get_categories_kb())
    await state.set_state(DeleteCategory.waiting_category)

@router.message(DeleteCategory.waiting_category)
async def delete_category_confirm(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if message.text not in cats:
        await message.answer("❌ Выберите категорию из списка.")
        return
    await state.update_data(category=message.text)
    await message.answer(f"Подтвердите удаление категории '{message.text}':", reply_markup=get_confirm_delete_kb())
    await state.set_state(DeleteCategory.waiting_confirm)

# --- Удаление вопроса ---
@router.message(AdminMenu.delete_submenu, F.text == "🗑 Вопрос")
async def delete_faq_start(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if not cats:
        await message.answer("❌ Категории отсутствуют", reply_markup=get_admin_main_menu_kb())
        await state.set_state(AdminMenu.menu)
        return
    await message.answer("Выберите категорию:", reply_markup=await get_categories_kb())
    await state.set_state(DeleteFAQ.waiting_category)

@router.message(DeleteFAQ.waiting_category)
async def delete_faq_category(message: types.Message, state: FSMContext):
    cats = await get_all_categories()
    if message.text not in cats:
        await message.answer("❌ Выберите категорию из списка.")
        return
    await state.update_data(category=message.text)
    await message.answer("Выберите вопрос для удаления:", reply_markup=await get_questions_kb(message.text))
    await state.set_state(DeleteFAQ.waiting_question)

@router.message(DeleteFAQ.waiting_question)
async def delete_faq_confirm(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data["category"]
    questions = await get_faq_by_category(category)
    if message.text not in questions:
        await message.answer("❌ Выберите вопрос из списка.")
        return
    await state.update_data(question=message.text)
    await message.answer(f"Подтвердите удаление вопроса '{message.text}':", reply_markup=get_confirm_delete_kb())
    await state.set_state(DeleteFAQ.waiting_confirm)

# --- Обработка подтверждения удаления ---
@router.callback_query(F.data.startswith("confirm_delete_"))
async def handle_confirm_delete(call: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    await call.answer()

    if current_state == "DeleteCategory:waiting_confirm":
        category = data.get("category")
        if call.data == "confirm_delete_yes":
            success = await delete_category(category)
            if success:
                await call.message.edit_text(f"✅ Категория '{category}' удалена.")
            else:
                await call.message.edit_text("❌ Ошибка при удалении категории.")
        else:
            await call.message.edit_text("Удаление отменено.")
        await state.clear()

    elif current_state == "DeleteFAQ:waiting_confirm":
        category = data.get("category")
        question = data.get("question")
        if call.data == "confirm_delete_yes":
            success = await delete_question(category, question)
            if success:
                await call.message.edit_text(f"✅ Вопрос '{question}' удалён.")
            else:
                await call.message.edit_text("❌ Ошибка при удалении вопроса.")
        else:
            await call.message.edit_text("Удаление отменено.")
        await state.clear()

    else:
        await call.message.answer("⚠️ Неподдерживаемое действие.")

# --- Управление админами ---
@router.message(AdminMenu.admin_management, F.text == "➕ Добавить админа")
async def add_admin_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ID пользователя для добавления в админы:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AdminManagement.add_admin)

@router.message(AdminManagement.add_admin)
async def add_admin_process(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный числовой ID.")
        return
    admins = load_admins()
    if user_id in admins:
        await message.answer("❌ Этот пользователь уже является админом.")
        return
    admins.append(user_id)
    save_admins(admins)
    global ADMIN_IDS
    ADMIN_IDS = admins
    await message.answer(f"✅ Пользователь с ID {user_id} добавлен в админы.", reply_markup=get_admin_main_menu_kb())
    await state.set_state(AdminMenu.menu)

@router.message(AdminMenu.admin_management, F.text == "🗑 Удалить админа")
async def delete_admin_start(message: types.Message, state: FSMContext):
    admins = load_admins()
    if not admins:
        await message.answer("❌ Список админов пуст.", reply_markup=get_admin_main_menu_kb())
        await state.set_state(AdminMenu.menu)
        return
    admins_str = "\n".join(str(admin) for admin in admins)
    await message.answer(f"Текущие админы:\n{admins_str}\n\nВведите ID для удаления:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AdminManagement.delete_admin)

@router.message(AdminManagement.delete_admin)
async def delete_admin_process(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный числовой ID.")
        return
    admins = load_admins()
    if user_id not in admins:
        await message.answer("❌ Пользователь с таким ID не найден в списке админов.")
        return
    admins.remove(user_id)
    save_admins(admins)
    global ADMIN_IDS
    ADMIN_IDS = admins
    await message.answer(f"✅ Пользователь с ID {user_id} удалён из админов.", reply_markup=get_admin_main_menu_kb())
    await state.set_state(AdminMenu.menu)

# --- Обработчик кнопки "Назад" для всех состояний ---
@router.message(F.text == "⬅️ Назад")
async def back_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None or current_state == AdminMenu.menu.state:
        await message.answer("Вы уже в главном меню.", reply_markup=get_admin_main_menu_kb())
    else:
        await state.clear()
        await admin_menu(message, state)