"""Kutilmagan xatoliklarni ushlash: bot to'xtab qolmaydi, foydalanuvchiga xabar beriladi."""
import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from services.misc import texts

logger = logging.getLogger(__name__)

router = Router(name="errors")


@router.errors()
async def on_error(event: ErrorEvent) -> bool:
    update = event.update
    logger.error(
        "Update #%s ni qayta ishlashda xatolik: %r",
        update.update_id,
        event.exception,
        exc_info=event.exception,
    )
    try:
        if update.message is not None:
            await update.message.answer(texts.ERROR_GENERIC)
        elif update.callback_query is not None:
            await update.callback_query.answer(texts.ERROR_ALERT, show_alert=True)
    except Exception:  # xatolik haqida xabar berib bo'lmasa ham bot ishlashda davom etadi
        pass
    return True
