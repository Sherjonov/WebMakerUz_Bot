"""Admin paneli: mijozlar ro'yxati (/mijozlar) va botni mijoz sifatida sinab ko'rish."""
import contextlib
import math

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from config.config import CUSTOMERS_PER_PAGE
from filters import IsAdmin
from keyboards.inline import NOOP, PageCb, pages_kb
from services.db_api import db
from services.flow import begin_form
from services.misc import texts
from services.misc.formatting import customers_page_text

router = Router(name="admins.panel")
router.message.filter(F.chat.type == ChatType.PRIVATE, IsAdmin())
router.callback_query.filter(IsAdmin())


async def _build_page(page: int) -> tuple[str, InlineKeyboardMarkup | None]:
    total = await db.count_customers()
    if total == 0:
        return texts.NO_CUSTOMERS, None
    pages = max(1, math.ceil(total / CUSTOMERS_PER_PAGE))
    page = min(max(page, 0), pages - 1)
    rows = await db.list_customers(CUSTOMERS_PER_PAGE, page * CUSTOMERS_PER_PAGE)
    markup = pages_kb(page, pages) if pages > 1 else None
    return customers_page_text(rows, total, page, pages), markup


@router.message(Command("mijozlar"))
@router.message(F.text == texts.BTN_ADMIN_CUSTOMERS)
async def cmd_customers(message: Message) -> None:
    text, markup = await _build_page(0)
    await message.answer(text, reply_markup=markup)


@router.callback_query(PageCb.filter())
async def cb_page(callback: CallbackQuery, callback_data: PageCb) -> None:
    text, markup = await _build_page(callback_data.page)
    if isinstance(callback.message, Message):
        # matn o'zgarmagan bo'lsa Telegram xato qaytaradi — e'tibor bermaymiz
        with contextlib.suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data == NOOP)
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.message(F.text == texts.BTN_ADMIN_TEST)
async def admin_test(message: Message, state: FSMContext) -> None:
    """Admin botni oddiy mijoz kabi sinab ko'rishi uchun."""
    customer = await db.get_customer_by_tg(message.from_user.id)
    await begin_form(message, state, customer)
