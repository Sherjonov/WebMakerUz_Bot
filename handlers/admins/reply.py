"""Admin -> mijoz yozishmasi.

/5 yoki "Javob yozish" tugmasi -> suhbat rejimi: admin yozgan har bir xabar 5-raqamli mijozga yuboriladi.
"Suhbatni tugatish" tugmasi bilan rejimdan chiqiladi."""
import logging
import re

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from filters import IsAdmin, NotCommand
from keyboards.default import admin_chat_kb, admin_menu_kb
from keyboards.inline import ReplyCb
from services.db_api import db
from services.messaging import deliver_admin_message
from services.misc import texts
from services.misc.formatting import customer_card, esc
from states import AdminChat

logger = logging.getLogger(__name__)

router = Router(name="admins.reply")
router.message.filter(F.chat.type == ChatType.PRIVATE, IsAdmin())
router.callback_query.filter(IsAdmin())

_NUMBER = re.compile(r"^\d+$")


async def _open_chat(target: Message, state: FSMContext, customer_id: int) -> None:
    customer = await db.get_customer(customer_id)
    if customer is None:
        await target.answer(texts.CUSTOMER_NOT_FOUND)
        return
    await state.clear()
    await state.set_state(AdminChat.chatting)
    await state.update_data(customer_id=customer_id)
    card = customer_card(
        customer,
        await db.count_orders(customer_id),
        await db.latest_order(customer_id),
        await db.latest_delivery(customer_id),
    )
    await target.answer(card + texts.CHAT_HINT, reply_markup=admin_chat_kb())


@router.message(Command(_NUMBER))
async def cmd_customer_number(message: Message, command: CommandObject, state: FSMContext) -> None:
    digits = command.command
    if len(digits) > 12:  # SQLite butun son chegarasidan oshib ketmasligi uchun
        await message.answer(texts.CUSTOMER_NOT_FOUND)
        return
    await _open_chat(message, state, int(digits))


@router.callback_query(ReplyCb.filter())
async def cb_reply(callback: CallbackQuery, callback_data: ReplyCb, state: FSMContext) -> None:
    if isinstance(callback.message, Message):
        await _open_chat(callback.message, state, callback_data.customer_id)
    await callback.answer()


@router.message(F.text == texts.BTN_END_CHAT)
async def end_chat(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.CHAT_ENDED, reply_markup=admin_menu_kb())


@router.message(StateFilter(AdminChat.chatting), NotCommand())
async def chatting(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    customer = await db.get_customer(data.get("customer_id", 0))
    if customer is None:
        await state.clear()
        await message.answer(texts.CUSTOMER_NOT_FOUND, reply_markup=admin_menu_kb())
        return

    try:
        await deliver_admin_message(bot, message, customer["tg_id"])
    except TelegramForbiddenError:
        await message.answer(texts.BLOCKED)
        return
    except TelegramAPIError as e:
        logger.warning("Admin xabarini mijoz #%s ga yuborib bo'lmadi: %s", customer["id"], e)
        await message.answer(f"⚠️ Yuborib bo'lmadi: {esc(e.message)}")
        return
    await message.answer(texts.delivered(customer["id"]))
