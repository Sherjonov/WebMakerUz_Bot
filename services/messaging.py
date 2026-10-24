"""Mijoz <-> admin xabar almashinuvi uchun yordamchilar."""
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import Message, ReactionTypeEmoji

from config.config import ADMINS
from keyboards.inline import receipt_decision_kb, reply_kb
from services.db_api import db
from services.misc import texts
from services.misc.formatting import customer_message_header, esc, receipt_caption

logger = logging.getLogger(__name__)


async def react(bot: Bot, message: Message, emoji: str = "👌") -> bool:
    """Xabarga reaksiya qo'yadi (chatni to'ldirmaslik uchun). Muvaffaqiyatli bo'lsa True."""
    try:
        await bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reaction=[ReactionTypeEmoji(emoji=emoji)],
        )
        return True
    except TelegramAPIError:
        return False


async def deliver_admin_message(bot: Bot, admin_message: Message, customer_tg_id: int) -> None:
    """Admin yozgan xabarni (matn, rasm, fayl, ovoz ...) mijozga yetkazadi.

    Xatolik bo'lsa (masalan, mijoz botni bloklagan) TelegramAPIError ko'tariladi."""
    if admin_message.text:
        composed = f"{texts.ADMIN_MESSAGE_HEADER}\n\n{admin_message.html_text}"
        if len(composed) <= 4000:
            try:
                await bot.send_message(customer_tg_id, composed)
                return
            except TelegramBadRequest as e:
                if "parse" not in str(e).lower():
                    raise
                # Formatlashda muammo bo'lsa, pastda xabar nusxasi sifatida yuboriladi

    await bot.send_message(customer_tg_id, texts.ADMIN_MESSAGE_HEADER)
    await bot.copy_message(
        chat_id=customer_tg_id,
        from_chat_id=admin_message.chat.id,
        message_id=admin_message.message_id,
    )


async def forward_customer_message(bot: Bot, customer: dict, message: Message) -> int:
    """Mijoz yozgan xabarni barcha adminlarga '/N' sarlavhasi va 'Javob yozish' tugmasi bilan yuboradi.

    Xabar yetib borgan adminlar sonini qaytaradi."""
    header = customer_message_header(customer)
    markup = reply_kb(customer["id"])
    reached = 0
    for admin_id in ADMINS:
        try:
            body = esc(message.text) if message.text else None
            if body is not None and len(header) + 2 + len(body) <= 4000:
                await bot.send_message(admin_id, f"{header}\n\n{body}", reply_markup=markup)
            else:
                await bot.send_message(admin_id, header)
                await bot.copy_message(
                    chat_id=admin_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                    reply_markup=markup,
                )
            reached += 1
        except TelegramAPIError as e:
            logger.warning("Mijoz xabarini admin %s ga yuborib bo'lmadi: %s", admin_id, e)
    return reached


async def send_receipt_to_admins(
    bot: Bot, message: Message, customer: dict, order: dict, delivery: dict, receipt_id: int
) -> int:
    """Mijoz yuborgan chekni (rasm/fayl) adminlarga tasdiqlash tugmalari bilan yuboradi.

    Xabar yetib borgan adminlar sonini qaytaradi."""
    caption = receipt_caption(customer, order, delivery)
    markup = receipt_decision_kb(receipt_id)
    delivered = 0
    for admin_id in ADMINS:
        try:
            try:
                # Chekning o'zi + sarlavha + tugmalar — bitta xabarda
                copied = await bot.copy_message(
                    chat_id=admin_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                    caption=caption,
                    reply_markup=markup,
                )
                admin_message_id = copied.message_id
            except TelegramBadRequest:
                # Sarlavhali nusxa bo'lmasa: avval matn (tugmalar bilan), keyin chekning o'zi
                sent = await bot.send_message(admin_id, caption, reply_markup=markup)
                await bot.copy_message(
                    chat_id=admin_id, from_chat_id=message.chat.id, message_id=message.message_id
                )
                admin_message_id = sent.message_id
        except TelegramAPIError as e:
            logger.warning("Chekni admin %s ga yuborib bo'lmadi: %s", admin_id, e)
            continue
        await db.save_admin_message("receipt", receipt_id, admin_id, admin_message_id)
        delivered += 1
    return delivered
