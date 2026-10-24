"""Mijoz to'lovni amalga oshirgach «✅ Tayyor» ni bosadi va chek yuboradi (chek to'g'ridan-to'g'ri adminlarga ketadi)."""
from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.config import MAX_PENDING_RECEIPTS
from keyboards.default import cancel_kb, main_menu_for
from keyboards.inline import PayCb
from services.db_api import db
from services.messaging import send_receipt_to_admins
from services.misc import texts
from states import PaymentReceipt

router = Router(name="users.payment")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.callback_query(PayCb.filter())
async def cb_paid(callback: CallbackQuery, callback_data: PayCb, state: FSMContext, bot: Bot) -> None:
    customer = await db.get_customer_by_tg(callback.from_user.id)
    delivery = await db.get_delivery(callback_data.delivery_id)
    if customer is None or delivery is None or delivery["customer_id"] != customer["id"]:
        await callback.answer(texts.PAYMENT_NOT_FOUND, show_alert=True)
        return
    if delivery["status"] == "paid":
        await callback.answer(texts.PAYMENT_ALREADY_PAID, show_alert=True)
        return
    if delivery["status"] != "awaiting_payment":
        await callback.answer(texts.PAYMENT_STALE, show_alert=True)
        return

    await state.clear()
    await state.set_state(PaymentReceipt.waiting)
    await state.update_data(delivery_id=delivery["id"])
    await bot.send_message(
        callback.from_user.id, texts.SEND_RECEIPT, reply_markup=cancel_kb("Chek rasmini yuboring...")
    )
    await callback.answer()


@router.message(StateFilter(PaymentReceipt.waiting), F.photo | F.document)
async def got_receipt(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id
    data = await state.get_data()
    delivery = await db.get_delivery(data.get("delivery_id", 0))
    customer = await db.get_customer_by_tg(user_id)
    if delivery is None or customer is None or delivery["customer_id"] != customer["id"]:
        await state.clear()
        await message.answer(texts.PAYMENT_NOT_FOUND, reply_markup=main_menu_for(user_id))
        return
    if delivery["status"] != "awaiting_payment":
        await state.clear()
        note = texts.PAYMENT_ALREADY_PAID if delivery["status"] == "paid" else texts.PAYMENT_STALE
        await message.answer(note, reply_markup=main_menu_for(user_id))
        return
    if await db.count_pending_receipts(delivery["id"]) >= MAX_PENDING_RECEIPTS:
        await message.answer(texts.RECEIPT_TOO_MANY)
        return

    order = await db.get_order(delivery["order_id"])
    receipt_id = await db.create_receipt(delivery["id"])
    reached = await send_receipt_to_admins(bot, message, customer, order, delivery, receipt_id)
    if reached == 0:
        await db.delete_receipt(receipt_id)
        await message.answer(texts.RECEIPT_UNAVAILABLE)  # holat saqlanadi: mijoz qayta yuborishi mumkin
        return

    await state.clear()
    await message.answer(texts.RECEIPT_SENT, reply_markup=main_menu_for(user_id))


@router.message(StateFilter(PaymentReceipt.waiting))
async def receipt_other(message: Message) -> None:
    if message.text and message.text.startswith("/"):
        await message.answer(texts.unknown_command(False))
    else:
        await message.answer(texts.RECEIPT_EXPECTED)
