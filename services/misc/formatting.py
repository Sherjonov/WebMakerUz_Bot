"""Matnlarni formatlash yordamchilari. Hamma dinamik qiymatlar HTML uchun xavfsiz (escape) qilinadi."""
import html
from datetime import datetime

from config import config as cfg
from config.config import TASHKENT_TZ

_TS_FORMAT = "%Y-%m-%d %H:%M:%S"
NEGOTIABLE_PRICE = "Kelishiladi"  # narx "🤝 Kelishamiz" tanlanganda saqlanadigan qiymat
DESCRIPTION_CHUNK = 2600  # bitta xabarga sig'adigan tavsif bo'lagi (escape qilingandan keyin)


def esc(value: object) -> str:
    """HTML maxsus belgilarini (<, >, &) xavfsiz holatga keltiradi."""
    return html.escape(str(value), quote=False)


def now_str() -> str:
    return datetime.now(TASHKENT_TZ).strftime(_TS_FORMAT)


def short_dt(value: str) -> str:
    return value[:16]


def age_seconds(value: str) -> float:
    """now_str() formatidagi vaqtdan necha soniya o'tganini qaytaradi."""
    try:
        then = datetime.strptime(value, _TS_FORMAT).replace(tzinfo=TASHKENT_TZ)
    except (TypeError, ValueError):
        return float("inf")
    return (datetime.now(TASHKENT_TZ) - then).total_seconds()


def full_name(customer: dict) -> str:
    return f"{customer['first_name']} {customer['last_name']}".strip()


def username_view(value: str | None) -> str:
    return esc(value) if value else "—"


def status_view(status: str | None) -> str:
    return {"ready": "✅ tayyor", "new": "⏳ jarayonda"}.get(status or "", "—")


def escaped_chunks(raw: str, limit: int = DESCRIPTION_CHUNK) -> list[str]:
    """Matnni escape qilib, har biri `limit` belgidan oshmaydigan bo'laklarga bo'ladi.

    Imkon bo'lsa, bo'sh joy yoki qator oxirida bo'ladi."""
    raw = raw.strip()
    if not raw:
        return [""]
    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    for ch in raw:
        piece = html.escape(ch, quote=False)
        if size + len(piece) > limit:
            cut = len(buf)
            for i in range(len(buf) - 1, max(len(buf) - 400, -1), -1):
                if buf[i] in ("\n", " "):
                    cut = i + 1
                    break
            chunks.append("".join(buf[:cut]).strip())
            buf = buf[cut:]
            size = sum(len(p) for p in buf)
        buf.append(piece)
        size += len(piece)
    if buf:
        chunks.append("".join(buf).strip())
    return [c for c in chunks if c] or [""]


def customer_lines(c: dict) -> str:
    return (
        f"👤 <b>Ism:</b> {esc(c['first_name'])}\n"
        f"👥 <b>Familiya:</b> {esc(c['last_name'])}\n"
        f"📱 <b>Telefon:</b> {esc(c['phone'])}\n"
        f"🔗 <b>Telegram:</b> {username_view(c['username'])} · "
        f"<a href=\"tg://user?id={c['tg_id']}\">profil</a>\n"
        f"🆔 <b>ID:</b> <code>{c['tg_id']}</code>"
    )


def new_order_messages(customer: dict, order: dict, *, repeat: bool = False) -> list[str]:
    """Adminga yuboriladigan yangi buyurtma xabarlari (uzun matn bo'lsa bir nechta)."""
    cid = customer["id"]
    title = "🔁 <b>Yangi buyurtma</b> (mavjud mijoz)" if repeat else "🆕 <b>Yangi buyurtma</b>"
    head = (
        f"/{cid} — {title}\n\n"
        f"{customer_lines(customer)}\n"
        f"🕒 <b>Vaqt:</b> {short_dt(order['created_at'])}\n\n"
        f"💰 <b>Narx:</b> {esc(order['price'])}\n\n"
        "🌐 <b>Sayt haqida:</b>\n"
    )
    chunks = escaped_chunks(order["description"])
    messages = [head + f"<blockquote>{chunks[0]}</blockquote>"]
    for i, chunk in enumerate(chunks[1:], start=2):
        messages.append(
            f"/{cid} — 🌐 <b>Sayt haqida</b> (davomi {i}/{len(chunks)}):\n"
            f"<blockquote>{chunk}</blockquote>"
        )
    if order.get("attachments"):
        messages[-1] += f"\n\n📎 <b>Ilovalar:</b> {order['attachments']} ta (pastda)"
    return messages


def web_request_text(
    customer: dict,
    *,
    answer: str | None = None,
    admin_name: str | None = None,
    delivered: bool | None = None,
) -> str:
    text = (
        f"/{customer['id']} — <b>{esc(full_name(customer))}</b>\n\n"
        "🌐 <b>Sayt tayyor bo'ldimi?</b>"
    )
    if answer in ("yes", "no"):
        verdict = "✅ Ha" if answer == "yes" else "❌ Yo'q"
        who = f" — {esc(admin_name)}" if admin_name else ""
        text += f"\n\n<b>Javob: {verdict}</b>{who}"
        if delivered is True:
            text += "\n<i>(mijozga yuborildi)</i>"
        elif delivered is False:
            text += "\n<i>(⚠️ mijozga yetib bormadi)</i>"
    return text


def price_changed_text(customer: dict, old_price: str, new_price: str) -> str:
    return (
        f"/{customer['id']} — 💰 <b>Narx o'zgartirildi</b>\n\n"
        f"👤 <b>{esc(full_name(customer))}</b> · {esc(customer['phone'])}\n"
        f"📉 <b>Eski narx:</b> {esc(old_price)}\n"
        f"📈 <b>Yangi narx:</b> {esc(new_price)}"
    )


def customer_message_header(customer: dict) -> str:
    return f"💬 /{customer['id']} — <b>{esc(full_name(customer))}</b> yozdi:"


def customer_card(
    customer: dict, orders_count: int, last_order: dict | None, delivery: dict | None = None
) -> str:
    lines = [
        f"/{customer['id']} — 👤 <b>Mijoz kartasi</b>",
        "",
        customer_lines(customer),
        f"🕒 <b>Ro'yxatdan o'tgan:</b> {short_dt(customer['created_at'])}",
        f"📦 <b>Buyurtmalar soni:</b> {orders_count}",
    ]
    if last_order:
        desc = last_order["description"]
        shown = desc if len(desc) <= 500 else desc[:500].rstrip() + "…"
        lines += [
            "",
            f"🌐 <b>Oxirgi buyurtma</b> ({status_view(last_order['status'])}):",
            f"💰 <b>Narx:</b> {esc(last_order['price'])}",
            f"<blockquote>{esc(shown)}</blockquote>",
        ]
        if last_order.get("attachments"):
            lines.append(f"📎 Ilovalar: {last_order['attachments']} ta")
    if delivery:
        label = {"paid": "💰 to'langan", "awaiting_payment": "⏳ to'lov kutilmoqda", "cancelled": "🚫 bekor qilingan"}.get(
            delivery["status"], delivery["status"]
        )
        lines += ["", f"🔗 <b>Sayt havolasi:</b> {esc_short(delivery['link'], 120)} ({label})"]
    return "\n".join(lines)


def customers_page_text(rows: list[dict], total: int, page: int, pages: int) -> str:
    lines = [f"📋 <b>Mijozlar ro'yxati</b> — jami: <b>{total}</b>", ""]
    for c in rows:
        if c.get("last_delivery") == "paid":
            icon = "💰"
        else:
            icon = "✅" if c.get("last_status") == "ready" else "⏳"
        lines.append(f"/{c['id']} — <b>{esc(full_name(c))}</b> · {esc(c['phone'])} {icon}")
    lines += [
        "",
        f"<i>Sahifa {page + 1}/{pages}. Mijozga yozish uchun uning raqamini bosing.</i>",
        "<i>⏳ jarayonda · ✅ tayyor · 💰 to'langan</i>",
    ]
    return "\n".join(lines)


# ───────────── sayt yuklash / to'lov / chek ─────────────
def esc_short(raw: str, limit: int) -> str:
    """Uzun matnni `limit` belgigacha qisqartirib, HTML uchun xavfsiz qiladi."""
    raw = raw.strip()
    return esc(raw if len(raw) <= limit else raw[:limit].rstrip() + "…")


def format_card(number: str) -> str:
    """8600123456789012 -> 8600 1234 5678 9012"""
    return " ".join(number[i:i + 4] for i in range(0, len(number), 4))


def payment_request_text(customer: dict, order: dict, link: str) -> str:
    """Mijozga yuboriladigan to'lov so'rovi (karta raqami .env dan olinadi)."""
    owner = f" — {esc(cfg.CARD_OWNER)}" if cfg.CARD_OWNER else ""
    lines = [
        f"🎉 <b>Saytingiz tayyor, {esc(customer['first_name'])}!</b>",
        "",
        "💳 <b>To'lov uchun karta:</b>",
        f"<code>{esc(format_card(cfg.CARD_NUMBER))}</code>{owner}",
    ]
    if order["price"] != NEGOTIABLE_PRICE:
        lines += ["", f"💰 <b>Narx:</b> {esc(order['price'])}"]
    if cfg.SEND_LINK_BEFORE_PAYMENT:
        lines += ["", f"🌐 <b>Sayt:</b> {esc(link)}"]
    lines += [
        "",
        "To'lovni amalga oshirgach, pastdagi <b>«✅ Tayyor»</b> tugmasini bosing — so'ng chekni yuborasiz.",
    ]
    if not cfg.SEND_LINK_BEFORE_PAYMENT:
        lines.append("🔐 Sayt havolasi to'lov tasdiqlangach yuboriladi.")
    return "\n".join(lines)


def upload_summary(customer: dict, link: str, delivered: bool) -> str:
    """Havolani yuborgan adminga tasdiq."""
    text = (
        f"/{customer['id']} — 🌐 <b>Sayt havolasi saqlandi</b>\n\n"
        f"👤 <b>{esc(full_name(customer))}</b>\n"
        f"🔗 {esc(link)}\n\n"
    )
    if not delivered:
        return text + "⚠️ Mijoz botni bloklagan — to'lov so'rovi yetib bormadi."
    text += "💳 Mijozga <b>to'lov so'rovi</b> yuborildi."
    if not cfg.SEND_LINK_BEFORE_PAYMENT:
        text += "\n🔐 Havola to'lov tasdiqlangach unga yuboriladi."
    return text


def upload_notice(customer: dict, link: str, admin_name: str) -> str:
    """Boshqa adminlarga: kim qaysi mijoz uchun havola yubordi."""
    return (
        f"/{customer['id']} — 📤 <b>{esc(admin_name)}</b> sayt havolasini yubordi\n\n"
        f"👤 <b>{esc(full_name(customer))}</b>\n"
        f"🔗 {esc(link)}\n"
        "💳 Mijozga to'lov so'rovi ketdi."
    )


def receipt_caption(
    customer: dict,
    order: dict,
    delivery: dict,
    *,
    decision: str | None = None,
    admin_name: str | None = None,
) -> str:
    """Adminga boradigan chek xabarining matni (caption <= 1024 belgi bo'lishi uchun qisqartirilgan)."""
    text = (
        f"/{customer['id']} — 🧾 <b>To'lov cheki</b>\n\n"
        f"👤 <b>{esc(full_name(customer))}</b> · {esc(customer['phone'])}\n"
        f"💰 <b>Narx:</b> {esc_short(order['price'], 40)}\n"
        f"🌐 <b>Sayt:</b> {esc_short(delivery['link'], 60)}"
    )
    who = f" — {esc(admin_name)}" if admin_name else ""
    if decision == "approved":
        text += f"\n\n<b>✅ To'lov tasdiqlandi</b>{who}"
    elif decision == "rejected":
        text += f"\n\n<b>❌ Rad etildi</b>{who}"
    elif decision == "stale":
        text += "\n\n<i>🚫 Bu to'lov so'rovi eskirgan (yangi havola yuborilgan)</i>"
    else:
        text += "\n\nChek to'g'rimi? To'lovni tasdiqlaysizmi?"
    return text
