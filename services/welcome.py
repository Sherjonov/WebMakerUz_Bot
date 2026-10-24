"""/start dagi salomlashuv: rasm + chiroyli matn."""
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile

from config.config import WELCOME_PHOTO
from services.db_api import db
from services.misc import texts

logger = logging.getLogger(__name__)

_FILE_ID_KEY = "welcome_file_id"
_FINGERPRINT_KEY = "welcome_fingerprint"


def _fingerprint() -> str | None:
    """Rasm faylining 'barmoq izi' (hajmi + o'zgargan vaqti). Fayl almashtirilsa o'zgaradi."""
    try:
        stat = WELCOME_PHOTO.stat()
    except OSError:
        return None
    return f"{stat.st_size}:{stat.st_mtime_ns}"


async def send_welcome(bot: Bot, chat_id: int) -> None:
    """Rasmni caption bilan yuboradi.

    Birinchi yuborishdan so'ng Telegram bergan file_id saqlanadi (keyingi safar tezroq ishlaydi).
    assets/welcome.jpg almashtirilsa, bot buni o'zi payqab rasmni qaytadan yuklaydi."""
    caption = texts.WELCOME_CAPTION
    fingerprint = _fingerprint()

    file_id = await db.get_setting(_FILE_ID_KEY)
    if file_id and fingerprint is not None and await db.get_setting(_FINGERPRINT_KEY) == fingerprint:
        try:
            await bot.send_photo(chat_id, file_id, caption=caption)
            return
        except TelegramBadRequest:
            logger.info("Saqlangan file_id yaroqsiz — rasm qaytadan yuklanadi")

    try:
        sent = await bot.send_photo(chat_id, FSInputFile(WELCOME_PHOTO), caption=caption)
    except OSError as e:  # rasm fayli topilmasa ham bot ishlashda davom etadi
        logger.error("Salomlashuv rasmini o'qib bo'lmadi (%s): %s", WELCOME_PHOTO, e)
        await bot.send_message(chat_id, caption)
        return

    if sent.photo and fingerprint is not None:
        await db.set_setting(_FILE_ID_KEY, sent.photo[-1].file_id)
        await db.set_setting(_FINGERPRINT_KEY, fingerprint)
