"""Admin mijoz yuborgan to'lov chekini tasdiqlaydi yoki rad etadi."""
import contextlib
import logging

from aiogram import Bot, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from filters import IsAdmin
from keyboards.inline import ReceiptCb, repay_kb
from services.db_api import db
from services.misc import texts
from services.misc.formatting import receipt_caption

logger = logging.getLogger(__name__)

router = Router(name="admins.payments")
router.callback_query.filter(IsAdmin())


async def _edit_card(bot: Bot, chat_id: int, message_id: int, text: str) -> None:
    """Chek xabarini yangilaydi (tugmalar olib tashlanadi)."""
    try:
        await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=text)
    except TelegramBadRequest:
        # Chek matn ko'rinishida yuborilgan bo'lishi mumkin; xabar o'chirilgan yoki matn o'zgarmagan bo'lsa — e'tibor bermaymiz
        with contextlib.suppress(TelegramAPIError):
            await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
    except TelegramAPIError as e:
        logger.warning("Admin %s dagi chek xabarini yangilab bo'lmadi: %s", chat_id, e)


async def _refresh_cards(
    bot: Bot,
    receipt_id: int,
    customer: dict,
    order: dict,
    delivery: dict,
    *,
    decision: str,
    admin_name: str | None,
    fallback: Message | None,
) -> None:
    text = receipt_caption(customer, order, delivery, decision=decision, admin_name=admin_name)
    targets = [(m["admin_id"], m["message_id"]) for m in await db.get_admin_messages("receipt", receipt_id)]
    if fallback is not None and (fallback.chat.id, fallback.message_id) not in targets:
        targets.append((fallback.chat.id, fallback.message_id))
    for chat_id, message_id in targets:
        await _edit_card(bot, chat_id, message_id, text)


@router.callback_query(ReceiptCb.filter())
async def cb_receipt(callback: CallbackQuery, callback_data: ReceiptCb, bot: Bot) -> None:
    if callback_data.action not in ("ok", "no"):
        await callback.answer()
        return

    receipt = await db.get_receipt(callback_data.receipt_id)
    delivery = await db.get_delivery(receipt["delivery_id"]) if receipt else None
    customer = await db.get_customer(delivery["customer_id"]) if delivery else None
    order = await db.get_order(delivery["order_id"]) if delivery else None
    if not (receipt and delivery and customer and order):
        await callback.answer(texts.PAYMENT_NOT_FOUND, show_alert=True)
        return

    admin = callback.from_user
    fallback = callback.message if isinstance(callback.message, Message) else None
    approve = callback_data.action == "ok"

    if delivery["status"] == "cancelled":
        # Admin shu orada yangi havola yuborgan — eski to'lov so'rovi bekor
        await _refresh_cards(
            bot, receipt["id"], customer, order, delivery, decision="stale", admin_name=None, fallback=fallback
        )
        await callback.answer(texts.PAYMENT_STALE, show_alert=True)
        return

    decided = await db.decide_receipt(
        receipt["id"], "approved" if approve else "rejected", admin.id, admin.full_name
    )
    if not decided:
        # Boshqa admin bu chekni allaqachon ko'rib chiqqan
        receipt = await db.get_receipt(receipt["id"])
        await _refresh_cards(
            bot, receipt["id"], customer, order, delivery,
            decision=receipt["status"], admin_name=receipt["decided_by_name"], fallback=fallback,
        )
        await callback.answer(texts.RECEIPT_ALREADY_DECIDED, show_alert=True)
        return

    customer_text: str | None = None
    markup = None
    if approve:
        # mark_delivery_paid faqat birinchi chaqiruvda True qaytaradi: mijozga ikki marta yuborilmaydi
        if await db.mark_delivery_paid(delivery["id"]):
            customer_text = texts.payment_approved(delivery["link"])
    else:
        fresh = await db.get_delivery(delivery["id"])
        if fresh is not None and fresh["status"] == "awaiting_payment":
            customer_text = texts.RECEIPT_REJECTED
            markup = repay_kb(delivery["id"])

    delivered: bool | None = None
    if customer_text is not None:
        delivered = True
        try:
            await bot.send_message(customer["tg_id"], customer_text, reply_markup=markup)
        except TelegramAPIError as e:
            delivered = False
            logger.warning("Mijoz #%s ga to'lov natijasini yuborib bo'lmadi: %s", customer["id"], e)

    await _refresh_cards(
        bot, receipt["id"], customer, order, delivery,
        decision="approved" if approve else "rejected", admin_name=admin.full_name, fallback=fallback,
    )
    if delivered is False:
        await callback.answer(texts.RECEIPT_NOT_DELIVERED_ALERT, show_alert=True)
    else:
        await callback.answer(texts.RECEIPT_APPROVED_ALERT if approve else texts.RECEIPT_REJECTED_ALERT)
