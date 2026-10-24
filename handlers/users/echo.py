"""Ro'yxatdan o'tgan mijozning erkin yozgan xabarlari adminlarga yuboriladi + noma'lum buyruqlar."""
from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import StateFilter
from aiogram.types import Message

from config.config import ADMINS
from services.db_api import db
from services.flow import reply_not_registered
from services.messaging import forward_customer_message, react
from services.misc import texts

router = Router(name="users.echo")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message) -> None:
    await message.answer(texts.unknown_command(message.from_user.id in ADMINS))


@router.message(StateFilter(None))
async def customer_message(message: Message, bot: Bot) -> None:
    user = message.from_user
    if user.id in ADMINS:
        await message.answer(texts.ADMIN_HINT)
        return

    customer = await db.get_customer_by_tg(user.id)
    if customer is None:
        await reply_not_registered(message)
        return

    reached = await forward_customer_message(bot, customer, message)
    if reached == 0:
        await message.answer(texts.CANT_DELIVER)
    elif not await react(bot, message):
        await message.answer(texts.SENT_TO_ADMIN)
