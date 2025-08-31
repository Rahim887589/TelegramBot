from aiogram import types
from aiogram.fsm.context import FSMContext
from faq_data import faq

async def handle_faq(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("selected_category")
    question = message.text.strip()

    if not category or category not in faq:
        await message.answer("Пожалуйста, выберите категорию.")
        return

    answer = faq[category].get(question)
    if answer:
        await message.answer(f"<b>Ответ:</b> {answer}")
    else:
        await message.answer("Извините, я не знаю ответа на этот вопрос.")
