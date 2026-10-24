"""Adminlarga xabar yuborish."""
import logging

from collections.abc import Iterable

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup

from config.config import ADMINS

logger = logging.getLogger(__name__)


async def on_startup_notify(bot: Bot) -> None:
    """Bot ishga tushganda barcha adminlarga xabar yuboradi."""
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, "🚀 <b>WebMakerUz Bot ishga tushdi</b>")
        except TelegramForbiddenError:
            logger.warning("Admin %s botga hali /start bosmagan — unga xabar yuborib bo'lmadi", admin_id)
        except TelegramAPIError as e:
            logger.warning("Admin %s ga xabar yuborib bo'lmadi: %s", admin_id, e)


async def broadcast_to_admins(
    bot: Bot,
    messages: str | list[str],
    reply_markup: InlineKeyboardMarkup | None = None,
    exclude: Iterable[int] = (),
) -> dict[int, int]:
    """Barcha adminlarga (exclude dagilardan tashqari) xabar(lar) yuboradi. Tugma birinchi xabarga qo'yiladi.

    {admin_id: birinchi_xabar_id} qaytaradi (faqat xabar yetib borgan adminlar)."""
    if isinstance(messages, str):
        messages = [messages]

    delivered: dict[int, int] = {}
    skip = set(exclude)
    for admin_id in ADMINS:
        if admin_id in skip:
            continue
        for index, text in enumerate(messages):
            try:
                sent = await bot.send_message(
                    admin_id, text, reply_markup=reply_markup if index == 0 else None
                )
            except TelegramForbiddenError:
                logger.warning("Admin %s botga hali /start bosmagan — xabar yetmadi", admin_id)
                break
            except TelegramAPIError as e:
                logger.error("Admin %s ga xabar yuborib bo'lmadi: %s", admin_id, e)
                break
            if index == 0:
                delivered[admin_id] = sent.message_id
    return delivered
