"""WebMakerUz Bot — web saytlarga buyurtma yig'uvchi Telegram bot.

Ishga tushirish:  python main.py"""
import asyncio
import contextlib
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.utils.token import TokenValidationError

from config import config as cfg
from config.config import BOT_TOKEN
from handlers import router as main_router
from middlewares import ThrottlingMiddleware
from services.backup import send_backup, start_backup
from services.bot_profile import set_bot_profile
from services.db_api import db
from services.health_server import start_health_server, start_keep_alive
from services.misc import texts
from services.misc.logger import setup_logging
from services.notify_admins import on_startup_notify
from services.set_bot_commands import set_default_commands

logger = logging.getLogger(__name__)


def create_dispatcher() -> Dispatcher:
    # SimpleEventIsolation: bir foydalanuvchining xabarlari ketma-ket qayta ishlanadi
    # (masalan, rasm albomi yoki "Tayyor" tugmasini ikki marta bosish xatolik bermaydi)
    dp = Dispatcher(storage=MemoryStorage(), events_isolation=SimpleEventIsolation())
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.include_router(main_router)
    return dp


def startup_notes() -> list[str]:
    """Adminlarga ishga tushish xabari bilan birga yuboriladigan muhim ogohlantirishlar."""
    notes: list[str] = []
    if db.was_fresh:
        notes.append(texts.FRESH_DB_NOTE)
    if cfg.ON_RENDER and not os.getenv("DB_PATH"):
        notes.append(texts.EPHEMERAL_DISK_NOTE)
    return notes


async def shutdown_backup(bot: Bot) -> None:
    """Bot o'chirilishidan oldin (Render qayta ishga tushirishi, yangi versiya) oxirgi o'zgarishlarni zaxiralaymiz."""
    if not (cfg.BACKUP_ENABLED and db.dirty):
        return
    try:
        sent = await asyncio.wait_for(send_backup(bot, silent=True, auto=True), timeout=20)
        logger.info("O'chirishdan oldingi zaxira nusxa %s ta adminga yuborildi", sent)
    except Exception:  # noqa: BLE001 — o'chirish jarayoni har qanday holatda davom etishi kerak
        logger.warning("O'chirishdan oldingi zaxira nusxani yuborib bo'lmadi", exc_info=True)


async def main() -> None:
    setup_logging()
    await db.init()

    bot: Bot | None = None
    health = None
    background: list[asyncio.Task] = []
    try:
        # Render "Web Service" port ochilishini kutadi — shuning uchun serverni ENG BIRINCHI ochamiz
        health = await start_health_server()

        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = create_dispatcher()

        await bot.delete_webhook(drop_pending_updates=False)
        me = await bot.get_me()
        logger.info("Bot ishga tushdi: @%s", me.username)

        await set_default_commands(bot)
        await set_bot_profile(bot)
        await on_startup_notify(bot, startup_notes())

        background += [t for t in (start_keep_alive(), start_backup(bot)) if t is not None]
        await dp.start_polling(bot)
    except TokenValidationError:
        logger.error("BOT_TOKEN formati noto'g'ri. .env faylini tekshiring (namuna: 123456789:AAxxxx...).")
    except TelegramUnauthorizedError:
        logger.error("BOT_TOKEN noto'g'ri yoki bekor qilingan. .env faylini tekshiring.")
    except TelegramNetworkError as e:
        logger.error("Telegram serveriga ulanib bo'lmadi (internetni tekshiring): %s", e)
    finally:
        # Ma'lumotlar bazasi har doim yopilishi shart, aks holda dastur to'xtamay qolishi mumkin
        for task in background:
            task.cancel()
        for task in background:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        if bot is not None:
            await shutdown_backup(bot)
        if health is not None:
            await health.cleanup()
        if bot is not None:
            await bot.session.close()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
