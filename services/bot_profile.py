"""Bot profilidagi tavsif matnlari ("What can this bot do?" oynasidagi matn)."""
import hashlib
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from services.db_api import db
from services.misc import texts

logger = logging.getLogger(__name__)


async def set_bot_profile(bot: Bot) -> None:
    """Tavsif matnlarini o'rnatadi (faqat o'zgargan bo'lsa).

    Eslatma: tavsifdagi RASMni Bot API orqali o'rnatib bo'lmaydi — buni @BotFather orqali
    qo'lda qilish kerak (README ga qarang)."""
    digest = hashlib.sha256(
        f"{bot.id}\n{texts.PROFILE_DESCRIPTION}\n{texts.PROFILE_SHORT}".encode()
    ).hexdigest()
    if await db.get_setting("profile_hash") == digest:
        return
    try:
        await bot.set_my_description(description=texts.PROFILE_DESCRIPTION)
        await bot.set_my_short_description(short_description=texts.PROFILE_SHORT)
    except TelegramAPIError as e:
        logger.warning("Bot tavsifini o'rnatib bo'lmadi: %s", e)
        return
    await db.set_setting("profile_hash", digest)
    logger.info("Bot tavsifi yangilandi")
