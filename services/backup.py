"""Ma'lumotlar bazasi zaxirasi: adminlarga fayl sifatida yuboriladi, /restore bilan tiklanadi.

Render bepul tarifida fayllar bot qayta ishga tushganda (yoki yangi versiya yuklanganda) o'chib ketadi.
Zaxira nusxalar adminlar chatida qoladi — ma'lumotlar yo'qolmaydi."""
import asyncio
import logging
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile

from config import config as cfg
from services.db_api import db
from services.misc import texts

logger = logging.getLogger(__name__)


async def send_backup(
    bot: Bot, admin_ids: list[int] | None = None, *, silent: bool = True, auto: bool = False
) -> int:
    """Baza nusxasini adminlarga (yoki berilgan adminlarga) yuboradi. Yetib borgan adminlar sonini qaytaradi."""
    targets = list(admin_ids) if admin_ids else list(cfg.ADMINS)
    if auto:
        db.dirty = False  # nusxa olingandan keyingi o'zgarishlar yana "dirty" qiladi
    delivered = 0
    with tempfile.TemporaryDirectory() as tmp:
        stamp = datetime.now(cfg.TASHKENT_TZ).strftime("%Y-%m-%d_%H-%M")
        path = Path(tmp) / f"webmaker_zaxira_{stamp}.db"
        await db.backup_to(path)
        caption = texts.backup_caption(await db.stats())
        for admin_id in targets:
            try:
                await bot.send_document(
                    admin_id, FSInputFile(path), caption=caption, disable_notification=silent
                )
                delivered += 1
            except TelegramAPIError as e:
                logger.warning("Zaxira nusxani admin %s ga yuborib bo'lmadi: %s", admin_id, e)
    if auto and delivered == 0:
        db.dirty = True  # keyingi safar qayta urinamiz
    return delivered


async def backup_loop(bot: Bot) -> None:
    """Ma'lumot o'zgargan bo'lsa, har BACKUP_INTERVAL_MINUTES daqiqada adminlarga zaxira nusxa yuboradi."""
    interval = cfg.BACKUP_INTERVAL_MINUTES * 60
    while True:
        await asyncio.sleep(interval)
        if not db.dirty:
            continue
        try:
            await send_backup(bot, silent=True, auto=True)
        except Exception:  # noqa: BLE001 — zaxira vazifasi hech qachon to'xtab qolmasligi kerak
            logger.exception("Avtomatik zaxira yuborishda xatolik")


def start_backup(bot: Bot) -> asyncio.Task | None:
    if not cfg.BACKUP_ENABLED:
        return None
    logger.info("Avtomatik zaxira yoqildi: o'zgarish bo'lsa har %s daqiqada", cfg.BACKUP_INTERVAL_MINUTES)
    return asyncio.create_task(backup_loop(bot), name="backup")


def inspect_backup(path: Path) -> dict[str, int] | None:
    """Zaxira fayli haqiqiy bot bazasi ekanini tekshiradi. Yaroqsiz bo'lsa None."""
    try:
        con = sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            return None
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if not {"customers", "orders"} <= tables:
            return None
        return {
            "customers": con.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
            "orders": con.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        }
    except sqlite3.Error:
        return None
    finally:
        con.close()
