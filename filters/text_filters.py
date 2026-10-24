from aiogram.filters import BaseFilter
from aiogram.types import Message


class PlainText(BaseFilter):
    """Oddiy matn (buyruq emas)."""

    async def __call__(self, message: Message) -> bool:
        return bool(message.text) and not message.text.startswith("/")


class NotCommand(BaseFilter):
    """Har qanday xabar (matn, rasm, ovoz...), faqat '/' bilan boshlanadigan matn emas."""

    async def __call__(self, message: Message) -> bool:
        return not (message.text and message.text.startswith("/"))
