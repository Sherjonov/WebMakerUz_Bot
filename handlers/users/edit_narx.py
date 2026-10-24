"""/edit_narx — narxni o'zgartirish (o'zgarish adminga yuboriladi)."""
from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from filters import PlainText
from keyboards.default import main_menu_for, price_kb
from keyboards.inline import reply_kb
from services.db_api import db
from services.flow import reply_not_registered
from services.misc import texts
from services.misc.formatting import price_changed_text
from services.misc.validators import clean_price
from services.notify_admins import broadcast_to_admins
from states import EditPrice

router = Router(name="users.edit_narx")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(Command("edit_narx"))
@router.message(F.text == texts.BTN_EDIT_PRICE)
async def cmd_edit_price(message: Message, state: FSMContext) -> None:
    customer = await db.get_customer_by_tg(message.from_user.id)
    order = await db.latest_order(customer["id"]) if customer else None
    if customer is None or order is None:
        await reply_not_registered(message)
        return

    await state.clear()
    await state.set_state(EditPrice.price)
    await state.update_data(order_id=order["id"])
    await message.answer(texts.edit_price_prompt(order["price"]), reply_markup=price_kb())


@router.message(StateFilter(EditPrice.price), PlainText())
async def new_price(message: Message, state: FSMContext, bot: Bot) -> None:
    text = message.text
    price = texts.PRICE_NEGOTIABLE_VALUE if text == texts.BTN_NEGOTIABLE else clean_price(text)
    if price is None:
        await message.answer(texts.BAD_PRICE)
        return

    data = await state.get_data()
    order = await db.get_order(data.get("order_id", 0))
    customer = await db.get_customer_by_tg(message.from_user.id)
    if order is None or customer is None:
        await state.clear()
        await reply_not_registered(message)
        return

    old_price = order["price"]
    if price == old_price:
        await message.answer(texts.PRICE_SAME)
        return

    await db.update_order_price(order["id"], price)
    await state.clear()
    await message.answer(texts.PRICE_UPDATED, reply_markup=main_menu_for(message.from_user.id))
    await broadcast_to_admins(
        bot, price_changed_text(customer, old_price, price), reply_markup=reply_kb(customer["id"])
    )


@router.message(StateFilter(EditPrice.price))
async def new_price_invalid(message: Message) -> None:
    await message.answer(texts.BAD_PRICE)
