"""/start, bekor qilish va yangi buyurtma tugmasi."""
from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config.config import ADMINS
from keyboards.default import admin_menu_kb, main_menu_for, start_kb, user_menu_kb
from services.db_api import db
from services.flow import begin_form, reply_not_registered
from services.misc import texts
from services.set_bot_commands import refresh_admin_commands
from services.welcome import send_welcome

router = Router(name="users.start")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(CommandStart())
@router.message(F.text == texts.BTN_START)
async def cmd_start(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()
    user = message.from_user
    await send_welcome(bot, message.chat.id)

    if user.id in ADMINS:
        await message.answer(texts.ADMIN_PANEL, reply_markup=admin_menu_kb())
        # Admin chati endi aniq mavjud — uning buyruqlar menyusini (/1, /2 ...) yangilaymiz
        await refresh_admin_commands(bot, [user.id])
        return

    customer = await db.get_customer_by_tg(user.id)
    if customer is not None:
        await message.answer(texts.welcome_back(customer["first_name"]), reply_markup=user_menu_kb())
        return

    await begin_form(message, state, None)


@router.message(Command("cancel"))
@router.message(F.text == texts.BTN_CANCEL)
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    if user_id in ADMINS or await db.get_customer_by_tg(user_id) is not None:
        await message.answer(texts.CANCELLED, reply_markup=main_menu_for(user_id))
    else:
        await message.answer(texts.CANCELLED_NEW, reply_markup=start_kb())


@router.message(F.text == texts.BTN_NEW_ORDER)
async def new_order(message: Message, state: FSMContext) -> None:
    customer = await db.get_customer_by_tg(message.from_user.id)
    if customer is None:
        await reply_not_registered(message)
        return
    await begin_form(message, state, customer)
