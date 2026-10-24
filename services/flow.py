"""Buyurtma formasini boshlash (mijoz va admin-sinov uchun umumiy)."""
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config.config import ADMINS
from keyboards.default import admin_menu_kb, details_kb, first_name_kb, start_kb
from services.misc import texts
from states import OrderForm


async def begin_form(message: Message, state: FSMContext, customer: dict | None) -> None:
    """customer=None -> to'liq ro'yxatdan o'tish (ism, familiya, telefon, username, sayt, narx).
    customer berilgan bo'lsa -> faqat yangi buyurtma (sayt haqida + narx)."""
    await state.clear()
    base = {"desc_parts": [], "attach": [], "count": 0}
    user = message.from_user

    if customer is None:
        await state.set_state(OrderForm.first_name)
        await state.update_data(customer_id=None, **base)
        await message.answer(
            f"{texts.hello(user.first_name)}\n\n{texts.step_first_name()}",
            reply_markup=first_name_kb(user.first_name),
        )
    else:
        await state.set_state(OrderForm.details)
        await state.update_data(customer_id=customer["id"], **base)
        await message.answer(texts.new_order_intro(1, 2), reply_markup=details_kb())


async def reply_not_registered(message: Message) -> None:
    """Ro'yxatdan o'tmagan foydalanuvchiga tushuntirish (mijoz va admin uchun alohida)."""
    if message.from_user.id in ADMINS:
        await message.answer(texts.ADMIN_NOT_CUSTOMER, reply_markup=admin_menu_kb())
    else:
        await message.answer(texts.NOT_REGISTERED, reply_markup=start_kb())
