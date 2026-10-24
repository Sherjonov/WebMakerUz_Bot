"""Inline klaviaturalar."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.inline.callbacks import PageCb, PayCb, ReceiptCb, ReplyCb, WebAnswerCb
from keyboards.styles import DANGER, PRIMARY, SUCCESS
from services.misc import texts

NOOP = "noop"


def reply_kb(customer_id: int) -> InlineKeyboardMarkup:
    """Admin uchun: mijozga javob yozish tugmasi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{texts.INL_REPLY} (/{customer_id})",
                    callback_data=ReplyCb(customer_id=customer_id).pack(),
                    style=PRIMARY,
                )
            ]
        ]
    )


def web_answer_kb(request_id: int) -> InlineKeyboardMarkup:
    """Admin uchun: 'Sayt tayyor bo'ldimi?' savoliga Ha / Yo'q."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.INL_YES,
                    callback_data=WebAnswerCb(request_id=request_id, answer="yes").pack(),
                    style=SUCCESS,
                ),
                InlineKeyboardButton(
                    text=texts.INL_NO,
                    callback_data=WebAnswerCb(request_id=request_id, answer="no").pack(),
                    style=DANGER,
                ),
            ]
        ]
    )


def pages_kb(page: int, pages: int) -> InlineKeyboardMarkup:
    """Mijozlar ro'yxati uchun sahifalash."""
    row: list[InlineKeyboardButton] = []
    if page > 0:
        row.append(
            InlineKeyboardButton(text=texts.INL_PREV, callback_data=PageCb(page=page - 1).pack(), style=PRIMARY)
        )
    row.append(InlineKeyboardButton(text=f"📄 {page + 1}/{pages}", callback_data=NOOP))
    if page < pages - 1:
        row.append(
            InlineKeyboardButton(text=texts.INL_NEXT, callback_data=PageCb(page=page + 1).pack(), style=PRIMARY)
        )
    return InlineKeyboardMarkup(inline_keyboard=[row])


def pay_kb(delivery_id: int) -> InlineKeyboardMarkup:
    """Mijoz uchun: to'lovdan keyin «✅ Tayyor» tugmasi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.INL_PAID,
                    callback_data=PayCb(delivery_id=delivery_id).pack(),
                    style=SUCCESS,
                )
            ]
        ]
    )


def repay_kb(delivery_id: int) -> InlineKeyboardMarkup:
    """Mijoz uchun: chek rad etilgach qayta yuborish tugmasi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.INL_REPAY,
                    callback_data=PayCb(delivery_id=delivery_id).pack(),
                    style=PRIMARY,
                )
            ]
        ]
    )


def receipt_decision_kb(receipt_id: int) -> InlineKeyboardMarkup:
    """Admin uchun: chekni tasdiqlash / rad etish."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.INL_APPROVE,
                    callback_data=ReceiptCb(receipt_id=receipt_id, action="ok").pack(),
                    style=SUCCESS,
                ),
                InlineKeyboardButton(
                    text=texts.INL_REJECT,
                    callback_data=ReceiptCb(receipt_id=receipt_id, action="no").pack(),
                    style=DANGER,
                ),
            ]
        ]
    )
