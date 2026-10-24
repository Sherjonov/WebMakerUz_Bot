"""Forma bosqichlaridagi (oddiy) klaviaturalar."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from keyboards.styles import DANGER, PRIMARY, SUCCESS
from services.misc import texts
from services.misc.validators import clean_name, normalize_username


def _markup(rows: list[list[KeyboardButton]], placeholder: str | None = None) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder=placeholder,
    )


def _cancel_row() -> list[KeyboardButton]:
    return [KeyboardButton(text=texts.BTN_CANCEL, style=DANGER)]


def cancel_kb(placeholder: str | None = None) -> ReplyKeyboardMarkup:
    return _markup([_cancel_row()], placeholder)


def first_name_kb(profile_first_name: str | None) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    suggestion = clean_name(profile_first_name)
    if suggestion:
        rows.append([KeyboardButton(text=suggestion, style=SUCCESS)])
    rows.append(_cancel_row())
    return _markup(rows, "Ismingiz...")


def last_name_kb(profile_last_name: str | None) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    suggestion = clean_name(profile_last_name)
    if suggestion:
        rows.append([KeyboardButton(text=suggestion, style=SUCCESS)])
    rows.append(_cancel_row())
    return _markup(rows, "Familiyangiz...")


def phone_kb() -> ReplyKeyboardMarkup:
    return _markup(
        [
            [KeyboardButton(text=texts.BTN_SHARE_PHONE, request_contact=True, style=SUCCESS)],
            _cancel_row(),
        ],
        "+998 90 123 45 67",
    )


def username_kb(profile_username: str | None) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    suggestion = normalize_username(profile_username)
    if suggestion:
        rows.append([KeyboardButton(text=suggestion, style=SUCCESS)])
    rows.append([KeyboardButton(text=texts.BTN_NO_USERNAME, style=PRIMARY)])
    rows.append(_cancel_row())
    return _markup(rows, "@username")


def details_kb() -> ReplyKeyboardMarkup:
    return _markup(
        [
            [KeyboardButton(text=texts.BTN_DONE, style=SUCCESS)],
            _cancel_row(),
        ],
        "Sayt haqida yozing...",
    )


def price_kb() -> ReplyKeyboardMarkup:
    return _markup(
        [
            [KeyboardButton(text=texts.BTN_NEGOTIABLE, style=PRIMARY)],
            _cancel_row(),
        ],
        "Masalan: 3 000 000 so'm",
    )
