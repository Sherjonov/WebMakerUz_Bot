"""Inline tugmalar uchun callback ma'lumotlari."""
from aiogram.filters.callback_data import CallbackData


class ReplyCb(CallbackData, prefix="reply"):
    customer_id: int


class WebAnswerCb(CallbackData, prefix="web"):
    request_id: int
    answer: str  # "yes" | "no"


class PageCb(CallbackData, prefix="cl"):
    page: int


class PayCb(CallbackData, prefix="pay"):
    """Mijoz «✅ Tayyor» (to'lov qildim) tugmasini bosdi."""
    delivery_id: int


class ReceiptCb(CallbackData, prefix="rcpt"):
    """Admin chekni tasdiqladi (ok) yoki rad etdi (no)."""
    receipt_id: int
    action: str  # "ok" | "no"
