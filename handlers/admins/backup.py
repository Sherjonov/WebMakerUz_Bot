"""/backup — bazaning zaxira nusxasi; /restore — zaxiradan tiklash."""
import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from filters import IsAdmin
from services.backup import inspect_backup, send_backup
from services.db_api import db
from services.misc import texts
from services.set_bot_commands import refresh_admin_commands

logger = logging.getLogger(__name__)

router = Router(name="admins.backup")
router.message.filter(F.chat.type == ChatType.PRIVATE, IsAdmin())

MAX_BACKUP_BYTES = 20 * 1024 * 1024  # Bot API orqali yuklab olish chegarasi


@router.message(Command("backup"))
async def cmd_backup(message: Message, bot: Bot) -> None:
    if await send_backup(bot, [message.from_user.id], silent=False) == 0:
        await message.answer(texts.BACKUP_FAILED)


@router.message(Command("restore"))
async def cmd_restore(message: Message, command: CommandObject, bot: Bot) -> None:
    # Zaxira fayliga javob sifatida yoki fayl sarlavhasida /restore yozilgan bo'lishi mumkin
    source = message.document or (message.reply_to_message.document if message.reply_to_message else None)
    if source is None:
        await message.answer(texts.RESTORE_HELP)
        return
    if not (source.file_name or "").lower().endswith(".db") or (source.file_size or 0) > MAX_BACKUP_BYTES:
        await message.answer(texts.RESTORE_BAD_FILE)
        return

    force = (command.args or "").strip().lower() == "force"
    current = await db.count_customers()
    if current > 0 and not force:
        await message.answer(texts.restore_needs_force(current))
        return

    incoming = db.path.with_name("restore_incoming.db")  # baza bilan bir papkada (bir diskda)
    try:
        await bot.download(source, destination=incoming)
    except (TelegramAPIError, OSError) as e:
        logger.warning("Zaxira faylini yuklab bo'lmadi: %s", e)
        incoming.unlink(missing_ok=True)
        await message.answer(texts.RESTORE_DOWNLOAD_FAILED)
        return

    info = await asyncio.to_thread(inspect_backup, incoming)
    if info is None:
        incoming.unlink(missing_ok=True)
        await message.answer(texts.RESTORE_BAD_FILE)
        return

    await db.replace_with(incoming)
    await refresh_admin_commands(bot)  # menyuga tiklangan mijozlar raqamlari qo'shiladi
    await message.answer(texts.restore_done(info))
    logger.warning("Baza zaxiradan tiklandi (admin %s): %s", message.from_user.id, info)
