from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from faq_data import faq
from admin_storage import load_admins

ADMIN_IDS = load_admins()

def get_main_kb(user_id):
    buttons = [[KeyboardButton(text=cat)] for cat in sorted(faq.keys())]
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="Админ")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
