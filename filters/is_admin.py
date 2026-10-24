from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from config.config import ADMINS


class IsAdmin(BaseFilter):
    """Xabar/tugma bosgan foydalanuvchi admin bo'lsa True."""

    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        return user is not None and user.id in ADMINS
