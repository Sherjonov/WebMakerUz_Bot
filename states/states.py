"""FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    """Ro'yxatdan o'tish + buyurtma (mavjud mijoz uchun faqat details va price)."""
    first_name = State()
    last_name = State()
    phone = State()
    username = State()
    details = State()
    price = State()


class EditPrice(StatesGroup):
    """/edit_narx"""
    price = State()


class AdminChat(StatesGroup):
    """Admin mijoz bilan yozishmoqda (/N)."""
    chatting = State()


class Upload(StatesGroup):
    """Admin sayt havolasini yubormoqda ("/5 https://...")."""
    link = State()


class PaymentReceipt(StatesGroup):
    """Mijoz to'lov chekini yubormoqda."""
    waiting = State()
