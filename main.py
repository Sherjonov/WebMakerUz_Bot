"""WebMakerUz Bot — web saytlarga buyurtma yig'uvchi Telegram bot.

Ishga tushirish:  python main.py"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.utils.token import TokenValidationError

from config.config import BOT_TOKEN
from handlers import router as main_router
from middlewares import ThrottlingMiddleware
from services.bot_profile import set_bot_profile
from services.db_api import db
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


async def main() -> None:
    setup_logging()
    await db.init()

    bot: Bot | None = None
    try:
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = create_dispatcher()

        await bot.delete_webhook(drop_pending_updates=False)
        me = await bot.get_me()
        logger.info("Bot ishga tushdi: @%s", me.username)

        await set_default_commands(bot)
        await set_bot_profile(bot)
        await on_startup_notify(bot)

        await dp.start_polling(bot)
    except TokenValidationError:
        logger.error("BOT_TOKEN formati noto'g'ri. .env faylini tekshiring (namuna: 123456789:AAxxxx...).")
    except TelegramUnauthorizedError:
        logger.error("BOT_TOKEN noto'g'ri yoki bekor qilingan. .env faylini tekshiring.")
    except TelegramNetworkError as e:
        logger.error("Telegram serveriga ulanib bo'lmadi (internetni tekshiring): %s", e)
    finally:
        # Ma'lumotlar bazasi har doim yopilishi shart, aks holda dastur to'xtamay qolishi mumkin
        if bot is not None:
            await bot.session.close()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
