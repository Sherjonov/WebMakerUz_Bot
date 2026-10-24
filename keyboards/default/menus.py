"""Asosiy menyu klaviaturalari."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from config.config import ADMINS
from keyboards.styles import DANGER, PRIMARY, SUCCESS
from services.misc import texts


def user_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=texts.BTN_STATUS, style=PRIMARY),
                KeyboardButton(text=texts.BTN_EDIT_PRICE, style=PRIMARY),
            ],
            [KeyboardButton(text=texts.BTN_NEW_ORDER, style=SUCCESS)],
        ],
        resize_keyboard=True,
    )


def start_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.BTN_START, style=SUCCESS)]],
        resize_keyboard=True,
    )


def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=texts.BTN_ADMIN_CUSTOMERS, style=PRIMARY),
                KeyboardButton(text=texts.BTN_ADMIN_UPLOAD, style=SUCCESS),
            ],
            [KeyboardButton(text=texts.BTN_ADMIN_TEST, style=PRIMARY)],
        ],
        resize_keyboard=True,
    )


def admin_chat_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.BTN_END_CHAT, style=DANGER)]],
        resize_keyboard=True,
        input_field_placeholder="Mijozga xabar yozing...",
    )


def main_menu_for(user_id: int) -> ReplyKeyboardMarkup:
    """Foydalanuvchiga mos asosiy menyu (admin yoki oddiy mijoz)."""
    return admin_menu_kb() if user_id in ADMINS else user_menu_kb()
