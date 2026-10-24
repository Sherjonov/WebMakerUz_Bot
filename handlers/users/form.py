"""Ro'yxatdan o'tish va buyurtma formasi (FSM).

Yangi mijoz: ism -> familiya -> telefon -> username -> sayt haqida -> narx.
Mavjud mijoz ("Yangi buyurtma"): sayt haqida -> narx."""
import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config.config import MAX_ATTACHMENTS, MAX_DESCRIPTION_CHARS
from filters import PlainText
from keyboards.default import details_kb, last_name_kb, main_menu_for, phone_kb, price_kb, username_kb
from keyboards.inline import reply_kb
from services.db_api import db
from services.messaging import react
from services.misc import texts
from services.misc.formatting import new_order_messages
from services.misc.validators import clean_name, clean_price, normalize_phone, normalize_username
from services.notify_admins import broadcast_to_admins
from services.set_bot_commands import refresh_admin_commands
from states import OrderForm

logger = logging.getLogger(__name__)

router = Router(name="users.form")
router.message.filter(F.chat.type == ChatType.PRIVATE)

MEDIA = F.photo | F.video | F.document | F.voice | F.audio | F.video_note | F.animation


def _steps(data: dict) -> tuple[int, int, int]:
    """(sayt_haqida_bosqichi, narx_bosqichi, jami) — yangi mijoz va mavjud mijoz uchun turlicha."""
    if data.get("customer_id") is None:
        return 5, 6, texts.TOTAL_STEPS_NEW
    return 1, 2, 2


# ───────────── 1. Ism ─────────────
@router.message(StateFilter(OrderForm.first_name), PlainText())
async def step_first_name(message: Message, state: FSMContext) -> None:
    name = clean_name(message.text)
    if name is None:
        await message.answer(texts.BAD_FIRST_NAME)
        return
    await state.update_data(first_name=name)
    await state.set_state(OrderForm.last_name)
    await message.answer(texts.step_last_name(), reply_markup=last_name_kb(message.from_user.last_name))


# ───────────── 2. Familiya ─────────────
@router.message(StateFilter(OrderForm.last_name), PlainText())
async def step_last_name(message: Message, state: FSMContext) -> None:
    name = clean_name(message.text)
    if name is None:
        await message.answer(texts.BAD_LAST_NAME)
        return
    await state.update_data(last_name=name)
    await state.set_state(OrderForm.phone)
    await message.answer(texts.step_phone(), reply_markup=phone_kb())


# ───────────── 3. Telefon (kontakt tugmasi yoki qo'lda yozish) ─────────────
async def _save_phone(message: Message, state: FSMContext, phone: str | None) -> None:
    if phone is None:
        await message.answer(texts.BAD_PHONE)
        return
    await state.update_data(phone=phone)
    await state.set_state(OrderForm.username)
    await message.answer(texts.step_username(), reply_markup=username_kb(message.from_user.username))


@router.message(StateFilter(OrderForm.phone), F.contact)
async def step_phone_contact(message: Message, state: FSMContext) -> None:
    await _save_phone(message, state, normalize_phone(message.contact.phone_number, from_contact=True))


@router.message(StateFilter(OrderForm.phone), PlainText())
async def step_phone_text(message: Message, state: FSMContext) -> None:
    await _save_phone(message, state, normalize_phone(message.text))


# ───────────── 4. Telegram username ─────────────
@router.message(StateFilter(OrderForm.username), PlainText())
async def step_username(message: Message, state: FSMContext) -> None:
    if message.text == texts.BTN_NO_USERNAME:
        username = ""
    else:
        username = normalize_username(message.text)
        if username is None:
            await message.answer(texts.BAD_USERNAME)
            return
    await state.update_data(username=username)
    await state.set_state(OrderForm.details)
    data = await state.get_data()
    number, _, total = _steps(data)
    await message.answer(texts.details_prompt(number, total), reply_markup=details_kb())


@router.message(StateFilter(OrderForm.first_name, OrderForm.last_name, OrderForm.phone, OrderForm.username))
async def text_steps_other(message: Message) -> None:
    await message.answer(texts.EXPECT_TEXT)


# ───────────── 5. Sayt haqida (bir nechta xabar + ilovalar, "Tayyor" bilan tugaydi) ─────────────
@router.message(StateFilter(OrderForm.details), F.text == texts.BTN_DONE)
async def details_done(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("desc_parts") and not data.get("attach"):
        await message.answer(texts.DETAILS_EMPTY)
        return
    await state.set_state(OrderForm.price)
    _, number, total = _steps(data)
    await message.answer(texts.price_prompt(number, total), reply_markup=price_kb())


async def _after_collect(
    message: Message, state: FSMContext, bot: Bot, *, desc_parts: list[str], attach: list[int]
) -> None:
    data = await state.get_data()
    first = data.get("count", 0) == 0
    await state.update_data(desc_parts=desc_parts, attach=attach, count=data.get("count", 0) + 1)
    # Birinchi xabarga matn bilan javob beramiz, keyingilariga esa reaksiya (chat to'lib ketmasligi uchun)
    if first or not await react(bot, message):
        await message.answer(texts.DETAILS_ACK)


@router.message(StateFilter(OrderForm.details), PlainText())
async def details_text(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    parts: list[str] = list(data.get("desc_parts", []))
    text = message.text.strip()
    if sum(len(p) for p in parts) + len(text) > MAX_DESCRIPTION_CHARS:
        await message.answer(texts.DETAILS_TOO_LONG)
        return
    parts.append(text)
    await _after_collect(message, state, bot, desc_parts=parts, attach=list(data.get("attach", [])))


@router.message(StateFilter(OrderForm.details), MEDIA)
async def details_media(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    attach: list[int] = list(data.get("attach", []))
    if len(attach) >= MAX_ATTACHMENTS:
        await message.answer(texts.TOO_MANY_FILES)
        return
    attach.append(message.message_id)
    await _after_collect(message, state, bot, desc_parts=list(data.get("desc_parts", [])), attach=attach)


@router.message(StateFilter(OrderForm.details))
async def details_other(message: Message) -> None:
    if message.text and message.text.startswith("/"):
        await message.answer(texts.unknown_command(False))
    else:
        await message.answer(texts.UNSUPPORTED)


# ───────────── 6. Narx va yakun ─────────────
@router.message(StateFilter(OrderForm.price), PlainText())
async def step_price(message: Message, state: FSMContext, bot: Bot) -> None:
    price = texts.PRICE_NEGOTIABLE_VALUE if message.text == texts.BTN_NEGOTIABLE else clean_price(message.text)
    if price is None:
        await message.answer(texts.BAD_PRICE)
        return
    await _finish_order(message, state, bot, price)


@router.message(StateFilter(OrderForm.price))
async def step_price_other(message: Message) -> None:
    await message.answer(texts.BAD_PRICE)


async def _finish_order(message: Message, state: FSMContext, bot: Bot, price: str) -> None:
    data = await state.get_data()
    parts: list[str] = data.get("desc_parts", [])
    attach: list[int] = data.get("attach", [])
    description = "\n\n".join(parts).strip() or texts.ATTACHMENT_ONLY
    user = message.from_user

    try:
        customer_id = data.get("customer_id")
        if customer_id is None:
            customer, order, created = await db.create_customer_with_order(
                tg_id=user.id,
                first_name=data["first_name"],
                last_name=data["last_name"],
                phone=data["phone"],
                username=data.get("username", ""),
                description=description,
                attachments=len(attach),
                price=price,
            )
        else:
            customer = await db.get_customer(customer_id)
            if customer is None:
                raise LookupError(f"mijoz #{customer_id} topilmadi")
            order = await db.add_order(customer_id, description, len(attach), price)
            created = False
    except (KeyError, LookupError):
        logger.exception("Buyurtmani saqlashda forma ma'lumotlari to'liq emas")
        await state.clear()
        await message.answer(texts.ERROR_GENERIC)
        return

    await state.clear()
    await message.answer(
        texts.order_accepted(customer["first_name"]), reply_markup=main_menu_for(user.id)
    )

    # Adminlarga: avval buyurtma kartasi (/N bilan), keyin mijoz yuborgan rasm/fayl/ovozlar
    sent = await broadcast_to_admins(
        bot, new_order_messages(customer, order, repeat=not created), reply_markup=reply_kb(customer["id"])
    )
    if not sent:
        logger.error(
            "Buyurtma #%s hech bir adminga yetib bormadi! Adminlar botga /start bosganini tekshiring.",
            order["id"],
        )
    for admin_id in sent:
        for message_id in attach:
            try:
                await bot.copy_message(
                    chat_id=admin_id, from_chat_id=message.chat.id, message_id=message_id
                )
            except TelegramAPIError as e:
                logger.warning("Ilovani admin %s ga yuborib bo'lmadi: %s", admin_id, e)

    if created:
        await refresh_admin_commands(bot)  # menyuga yangi mijoz raqami (/N) qo'shiladi
