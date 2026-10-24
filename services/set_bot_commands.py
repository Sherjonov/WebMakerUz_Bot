"""Bot buyruqlari menyusi ("/" bosilganda chiqadigan ro'yxat).

* Oddiy foydalanuvchilar: /start, /web, /edit_narx
* Adminlar: yuqoridagilar + /mijozlar + har bir mijoz raqami (/1, /2, ...).
  Mijoz raqamlari faqat adminlarning chatida ko'rinadi."""
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from config.config import ADMINS
from services.db_api import db
from services.misc.formatting import full_name

logger = logging.getLogger(__name__)

MAX_COMMANDS = 100  # Telegram chegarasi

CUSTOMER_COMMANDS = [
    BotCommand(command="start", description="🚀 Botni boshlash"),
    BotCommand(command="web", description="🌐 Sayt tayyor bo'ldimi?"),
    BotCommand(command="edit_narx", description="💰 Narxni o'zgartirish"),
]

ADMIN_COMMANDS = [
    BotCommand(command="mijozlar", description="📋 Barcha mijozlar ro'yxati"),
    BotCommand(command="yuklash", description="🌐 Web saytni yuklash"),
    *CUSTOMER_COMMANDS,
]


async def set_default_commands(bot: Bot) -> None:
    """Hamma uchun umumiy buyruqlar + adminlar uchun alohida ro'yxat."""
    await bot.set_my_commands(CUSTOMER_COMMANDS, scope=BotCommandScopeDefault())
    await refresh_admin_commands(bot)


async def refresh_admin_commands(bot: Bot, admin_ids: list[int] | None = None) -> None:
    """Adminlar menyusini yangilaydi: asosiy buyruqlar + eng so'nggi mijozlar raqamlari."""
    customers = await db.latest_customers(MAX_COMMANDS - len(ADMIN_COMMANDS))
    commands = list(ADMIN_COMMANDS)
    for customer in customers:
        commands.append(
            BotCommand(command=str(customer["id"]), description=f"👤 {full_name(customer)}"[:256])
        )

    for admin_id in admin_ids or ADMINS:
        scope = BotCommandScopeChat(chat_id=admin_id)
        try:
            await bot.set_my_commands(commands, scope=scope)
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                # Admin botga hali /start bosmagan — /start bosganda menyu yangilanadi
                logger.warning("Admin %s hali botga /start bosmagan: buyruqlar menyusi keyinroq o'rnatiladi", admin_id)
                continue
            # Telegram mijoz raqamlarini qabul qilmasa ham, asosiy buyruqlar menyusi buzilmasin
            logger.warning("Admin %s: mijoz raqamli menyu o'rnatilmadi (%s). Faqat asosiy buyruqlar o'rnatiladi", admin_id, e)
            try:
                await bot.set_my_commands(ADMIN_COMMANDS, scope=scope)
            except TelegramAPIError as e2:
                logger.warning("Admin %s uchun asosiy buyruqlarni o'rnatib bo'lmadi: %s", admin_id, e2)
        except TelegramAPIError as e:
            logger.warning("Admin %s uchun buyruqlar menyusini o'rnatib bo'lmadi: %s", admin_id, e)
