"""Admin: "Web saytni yuklash" — mijoz raqami va havolani yuboradi, mijozga to'lov so'rovi ketadi.

Format:  /5 https://sayt-manzili.uz   (5 — mijoz raqami, ketidan havola).
Mijoz havolani DARROV olmaydi: unga karta raqami bilan to'lov so'rovi boradi, havola esa admin chekni
tasdiqlagach yuboriladi (SEND_LINK_BEFORE_PAYMENT=true bo'lsa — to'lov so'rovi bilan birga)."""
import logging
import re

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import config as cfg
from filters import IsAdmin, NotCommand
from keyboards.default import admin_menu_kb, cancel_kb
from keyboards.inline import pay_kb
from services.db_api import db
from services.misc import texts
from services.misc.formatting import payment_request_text, upload_notice, upload_summary
from services.misc.validators import normalize_link
from services.notify_admins import broadcast_to_admins
from states import Upload

logger = logging.getLogger(__name__)

router = Router(name="admins.upload")
router.message.filter(F.chat.type == ChatType.PRIVATE, IsAdmin())

_NUMBER = re.compile(r"^\d+$")
# "/5 sayt.uz" yoki "/5 https://sayt.uz" — tugma bosilmasa ham ishlaydigan yorliq
_LINKISH = r"^(?:https?://)?[^\s/]+\.\S+$"


@router.message(Command("yuklash"))
@router.message(F.text == texts.BTN_ADMIN_UPLOAD)
async def ask_link(message: Message, state: FSMContext) -> None:
    if not cfg.payment_configured():
        await message.answer(texts.PAYMENT_NOT_CONFIGURED)
        return
    await state.clear()
    await state.set_state(Upload.link)
    await message.answer(texts.UPLOAD_PROMPT, reply_markup=cancel_kb("/5 https://sayt-manzili.uz"))


async def _process(message: Message, state: FSMContext, bot: Bot, number: str, raw_link: str | None) -> None:
    if not cfg.payment_configured():
        await message.answer(texts.PAYMENT_NOT_CONFIGURED)
        return

    customer = await db.get_customer(int(number)) if len(number) <= 12 else None
    if customer is None:
        await message.answer(texts.CUSTOMER_NOT_FOUND)
        return

    link = normalize_link(raw_link)
    if link is None:
        await message.answer(texts.UPLOAD_BAD_LINK)
        return

    order = await db.latest_order(customer["id"])
    if order is None:  # ro'yxatdan o'tgan mijozda buyurtma doim bo'ladi
        await message.answer(texts.CUSTOMER_NOT_FOUND)
        return

    delivery = await db.create_delivery(customer["id"], order["id"], link)
    await db.set_order_status(order["id"], "ready")
    await state.clear()

    # Mijozga: karta raqami bilan to'lov so'rovi + «✅ Tayyor» tugmasi
    delivered = True
    try:
        await bot.send_message(
            customer["tg_id"], payment_request_text(customer, order, link), reply_markup=pay_kb(delivery["id"])
        )
    except TelegramAPIError as e:
        delivered = False
        logger.warning("Mijoz #%s ga to'lov so'rovini yuborib bo'lmadi: %s", customer["id"], e)

    await message.answer(upload_summary(customer, link, delivered), reply_markup=admin_menu_kb())
    await broadcast_to_admins(
        bot, upload_notice(customer, link, message.from_user.full_name), exclude=[message.from_user.id]
    )


@router.message(StateFilter(Upload.link), Command(_NUMBER, magic=F.args))
async def upload_in_state(message: Message, command: CommandObject, state: FSMContext, bot: Bot) -> None:
    await _process(message, state, bot, command.command, command.args)


@router.message(Command(_NUMBER, magic=F.args.regexp(_LINKISH)))
async def upload_shortcut(message: Message, command: CommandObject, state: FSMContext, bot: Bot) -> None:
    await _process(message, state, bot, command.command, command.args)


@router.message(StateFilter(Upload.link), Command(_NUMBER))
async def upload_need_link(message: Message, command: CommandObject) -> None:
    await message.answer(texts.upload_need_link(command.command))


@router.message(StateFilter(Upload.link), NotCommand())
async def upload_format_hint(message: Message) -> None:
    await message.answer(texts.UPLOAD_FORMAT_HINT)
