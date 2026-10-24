"""Spamdan himoya: bir foydalanuvchi qisqa vaqtda juda ko'p xabar yubora olmaydi.

Chegara ataylab keng qilingan (10 soniyada 30 ta), shuning uchun rasm albomlari va
ketma-ket yozilgan bir nechta xabar bemalol o'tadi. Adminlarga chegara qo'yilmaydi."""
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config.config import ADMINS
from services.misc import texts

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 30, period: float = 10.0) -> None:
        self.limit = limit
        self.period = period
        self._hits: dict[int, deque[float]] = {}
        self._warned: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None or user.id in ADMINS:
            return await handler(event, data)

        now = time.monotonic()
        hits = self._hits.setdefault(user.id, deque())
        while hits and now - hits[0] > self.period:
            hits.popleft()

        if len(hits) >= self.limit:
            if now - self._warned.get(user.id, now - self.period - 1) > self.period:
                self._warned[user.id] = now
                logger.warning("Throttling: foydalanuvchi %s juda tez yozyapti", user.id)
                await self._warn(event)
            return None

        hits.append(now)
        if len(self._hits) > 5000:
            self._cleanup(now)
        return await handler(event, data)

    async def _warn(self, event: TelegramObject) -> None:
        try:
            if isinstance(event, (Message, CallbackQuery)):
                await event.answer(texts.TOO_FAST)
        except Exception:  # ogohlantirish yuborilmasa ham muammo emas
            pass

    def _cleanup(self, now: float) -> None:
        stale = [uid for uid, hits in self._hits.items() if not hits or now - hits[-1] > self.period]
        for uid in stale:
            self._hits.pop(uid, None)
            self._warned.pop(uid, None)
