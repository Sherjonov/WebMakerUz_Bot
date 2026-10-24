"""/web — "Sayt tayyor bo'ldimi?" so'rovi adminga yuboriladi (Ha / Yo'q tugmalari bilan)."""
from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from config.config import WEB_REQUEST_COOLDOWN
from keyboards.inline import web_answer_kb
from services.db_api import db
from services.flow import reply_not_registered
from services.misc import texts
from services.misc.formatting import age_seconds, web_request_text
from services.notify_admins import broadcast_to_admins

router = Router(name="users.web")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(Command("web"))
@router.message(F.text == texts.BTN_STATUS)
async def cmd_web(message: Message, bot: Bot) -> None:
    customer = await db.get_customer_by_tg(message.from_user.id)
    order = await db.latest_order(customer["id"]) if customer else None
    if customer is None or order is None:
        await reply_not_registered(message)
        return

    pending = await db.pending_web_request(order["id"])
    if pending is not None and age_seconds(pending["created_at"]) < WEB_REQUEST_COOLDOWN:
        await message.answer(texts.WEB_ALREADY_SENT)
        return

    request_id = await db.create_web_request(customer["id"], order["id"])
    sent = await broadcast_to_admins(
        bot, web_request_text(customer), reply_markup=web_answer_kb(request_id)
    )
    if not sent:
        await db.delete_web_request(request_id)
        await message.answer(texts.WEB_UNAVAILABLE)
        return

    for admin_id, message_id in sent.items():
        await db.save_admin_message("web", request_id, admin_id, message_id)
    await message.answer(texts.WEB_SENT)
