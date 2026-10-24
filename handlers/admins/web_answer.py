"""Admin "Sayt tayyor bo'ldimi?" savoliga Ha / Yo'q tugmasini bosadi -> javob mijozga ketadi."""
import logging

from aiogram import Bot, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from filters import IsAdmin
from keyboards.inline import WebAnswerCb
from services.db_api import db
from services.misc import texts
from services.misc.formatting import web_request_text

logger = logging.getLogger(__name__)

router = Router(name="admins.web_answer")
router.callback_query.filter(IsAdmin())


async def _refresh_admin_messages(
    bot: Bot, request: dict, customer: dict, delivered: bool | None, fallback: Message | None
) -> None:
    """Barcha adminlardagi savol xabarini yangilaydi (tugmalar olib tashlanadi, javob ko'rsatiladi)."""
    text = web_request_text(
        customer,
        answer=request["answer"],
        admin_name=request["answered_by_name"],
        delivered=delivered,
    )
    targets = [(m["admin_id"], m["message_id"]) for m in await db.get_admin_messages("web", request["id"])]
    if fallback is not None and (fallback.chat.id, fallback.message_id) not in targets:
        targets.append((fallback.chat.id, fallback.message_id))

    for chat_id, message_id in targets:
        try:
            # reply_markup berilmaydi -> eski inline tugmalar olib tashlanadi
            await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
        except TelegramBadRequest:
            pass  # xabar o'chirilgan yoki matn o'zgarmagan
        except TelegramAPIError as e:
            logger.warning("Admin %s dagi xabarni yangilab bo'lmadi: %s", chat_id, e)


@router.callback_query(WebAnswerCb.filter())
async def cb_web_answer(callback: CallbackQuery, callback_data: WebAnswerCb, bot: Bot) -> None:
    if callback_data.answer not in ("yes", "no"):
        await callback.answer()
        return

    request = await db.get_web_request(callback_data.request_id)
    customer = await db.get_customer(request["customer_id"]) if request else None
    if request is None or customer is None:
        await callback.answer(texts.WEB_REQUEST_NOT_FOUND, show_alert=True)
        return

    admin = callback.from_user
    fallback = callback.message if isinstance(callback.message, Message) else None

    updated = await db.answer_web_request(request["id"], callback_data.answer, admin.id, admin.full_name)
    if not updated:
        # Boshqa admin allaqachon javob bergan — ikki marta yubormaymiz
        request = await db.get_web_request(request["id"])
        await _refresh_admin_messages(bot, request, customer, None, fallback)
        await callback.answer(texts.WEB_ALREADY_ANSWERED, show_alert=True)
        return

    if callback_data.answer == "yes":
        await db.set_order_status(request["order_id"], "ready")
        customer_text = texts.WEB_READY
    else:
        await db.set_order_status(request["order_id"], "new")
        customer_text = texts.WEB_NOT_READY

    delivered = True
    try:
        await bot.send_message(customer["tg_id"], customer_text)
    except TelegramAPIError as e:
        delivered = False
        logger.warning("Mijoz #%s ga /web javobini yuborib bo'lmadi: %s", customer["id"], e)

    request = await db.get_web_request(request["id"])
    await _refresh_admin_messages(bot, request, customer, delivered, fallback)
    await callback.answer(
        texts.WEB_ANSWER_SENT if delivered else texts.WEB_ANSWER_BLOCKED, show_alert=not delivered
    )
