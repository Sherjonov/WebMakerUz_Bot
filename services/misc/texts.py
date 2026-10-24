"""Botdagi barcha matnlar shu yerda (tahrirlash oson bo'lishi uchun). Parse mode: HTML."""
from services.misc.formatting import NEGOTIABLE_PRICE, esc

# ═══════════════ Tugma matnlari ═══════════════
BTN_CANCEL = "❌ Bekor qilish"
BTN_DONE = "✅ Tayyor"
BTN_SHARE_PHONE = "📱 Raqamni yuborish"
BTN_NO_USERNAME = "🚫 Usernamem yo'q"
BTN_NEGOTIABLE = "🤝 Kelishamiz"
BTN_START = "🚀 Boshlash"
BTN_STATUS = "🌐 Sayt holati"
BTN_EDIT_PRICE = "💰 Narxni o'zgartirish"
BTN_NEW_ORDER = "🆕 Yangi buyurtma"
BTN_ADMIN_CUSTOMERS = "📋 Mijozlar"
BTN_ADMIN_TEST = "🧪 Mijoz sifatida sinash"
BTN_END_CHAT = "🔚 Suhbatni tugatish"

INL_REPLY = "✍️ Javob yozish"
INL_YES = "✅ Ha"
INL_NO = "❌ Yo'q"
INL_PREV = "⬅️ Oldingi"
INL_NEXT = "Keyingi ➡️"

PRICE_NEGOTIABLE_VALUE = NEGOTIABLE_PRICE

# ═══════════════ Bot profili (BotFather'dagi "Description") ═══════════════
PROFILE_DESCRIPTION = (
    "🌐 WebMakerUz — web saytlarni yaratib beramiz!\n\n"
    "Biz sizga zamonaviy, tez va ishonchli web saytlarni yaratib beramiz:\n"
    "🚀 Landing va vizitka saytlar\n"
    "🛒 Internet-do'konlar\n"
    "💼 Portfolio va korporativ saytlar\n"
    "📱 Barcha qurilmalarga moslashuvchan dizayn\n\n"
    "Buyurtma berish uchun START tugmasini bosing 👇"
)
PROFILE_SHORT = "🌐 Web saytlarni yaratib beramiz: landing, internet-do'kon, portfolio. Buyurtma qoldiring!"

# ═══════════════ /start ═══════════════
WELCOME_CAPTION = (
    "🌐 <b>WebMakerUz Bot</b>\n"
    "<i>Web sayt yaratishni oson va aqlli qiling!</i>\n\n"
    "Biz sizga <b>zamonaviy, tez va ishonchli</b> web saytlarni yaratib beramiz:\n\n"
    "🚀 <b>Tez va samarali</b> — saytingiz qisqa muddatda tayyor\n"
    "📱 <b>Moslashuvchan</b> — barcha qurilmalarda mukammal ko'rinish\n"
    "🛡 <b>Xavfsiz va ishonchli</b> — eng yaxshi xavfsizlik standartlari\n"
    "✨ <b>Zamonaviy dizayn</b> — chiroyli va professional shablonlar\n\n"
    "👇 Buyurtma berish uchun bir necha savolga javob bering — admin siz bilan tez orada bog'lanadi."
)


def hello(first_name: str) -> str:
    return (
        f"👋 <b>Salom, {esc(first_name)}!</b>\n\n"
        "Buyurtma berish uchun avval o'zingiz haqingizda qisqacha ma'lumot qoldiring:\n\n"
        "👤 Ism  •  👥 Familiya  •  📱 Telefon raqam  •  🔗 Telegram username\n\n"
        "Boshladik! 👇"
    )


def welcome_back(first_name: str) -> str:
    return (
        f"👋 <b>Xush kelibsiz, {esc(first_name)}!</b>\n\n"
        "Siz allaqachon ro'yxatdan o'tgansiz. Quyidagi tugmalardan foydalaning 👇\n\n"
        "🌐 /web — sayt tayyor bo'ldimi?\n"
        "💰 /edit_narx — narxni o'zgartirish\n"
        "💬 Admin bilan gaplashish uchun shunchaki xabar yozing."
    )


# ═══════════════ Ro'yxatdan o'tish / buyurtma formasi ═══════════════
TOTAL_STEPS_NEW = 6


def step_first_name() -> str:
    return f"👤 <b>1/{TOTAL_STEPS_NEW} — Ismingizni kiriting</b>\n<i>Masalan: Sardor</i>"


def step_last_name() -> str:
    return f"👥 <b>2/{TOTAL_STEPS_NEW} — Familiyangizni kiriting</b>\n<i>Masalan: Karimov</i>"


def step_phone() -> str:
    return (
        f"📱 <b>3/{TOTAL_STEPS_NEW} — Telefon raqamingizni yuboring</b>\n"
        "Pastdagi yashil tugmani bosing yoki raqamni o'zingiz yozing.\n"
        "<i>Masalan: +998 90 123 45 67</i>"
    )


def step_username() -> str:
    return (
        f"🔗 <b>4/{TOTAL_STEPS_NEW} — Telegram username'ingizni kiriting</b>\n"
        "<i>Masalan: @sardor_dev</i>"
    )


def details_prompt(n: int, total: int) -> str:
    return (
        f"🌐 <b>{n}/{total} — Sizga qanday sayt kerak?</b>\n\n"
        "Sayt haqida <b>barcha ma'lumotlarni to'liq</b> qoldiring — shunda sizga aniq va tez javob beramiz:\n\n"
        "▫️ Sayt turi: landing page, internet-do'kon, portfolio, korporativ sayt...\n"
        "▫️ Biznesingiz yoki sohangiz va saytning maqsadi\n"
        "▫️ Kerakli sahifalar va funksiyalar (to'lov, tillar, admin panel, bot...)\n"
        "▫️ Dizayn: ranglar, logotip, yoqqan namuna saytlar\n"
        "▫️ Muddat va qo'shimcha istaklaringiz\n\n"
        "💡 Matn, rasm, fayl yoki ovozli xabar yuborishingiz mumkin. Bir nechta xabar yozsangiz ham bo'ladi.\n"
        "Tugatgach, <b>«✅ Tayyor»</b> tugmasini bosing."
    )


def price_prompt(n: int, total: int) -> str:
    return (
        f"💰 <b>{n}/{total} — Narxni qoldiring</b>\n\n"
        "Sayt uchun qancha budjet ajratgansiz? Narxni yozing.\n"
        "<i>Masalan: 3 000 000 so'm yoki 300$</i>\n\n"
        "Narxni hali bilmasangiz — <b>«🤝 Kelishamiz»</b> tugmasini bosing."
    )


def new_order_intro(n: int, total: int) -> str:
    return "🆕 <b>Yangi buyurtma</b>\n\n" + details_prompt(n, total)


DETAILS_ACK = (
    "✅ Qabul qilindi! Yana ma'lumot qo'shishingiz mumkin.\n"
    "Tugatgach, <b>«✅ Tayyor»</b> tugmasini bosing."
)
DETAILS_EMPTY = (
    "❗️ Avval sayt haqida ma'lumot yuboring (matn, rasm, fayl yoki ovozli xabar), "
    "so'ng <b>«✅ Tayyor»</b> tugmasini bosing."
)
DETAILS_TOO_LONG = (
    "⚠️ Matn juda uzun bo'lib ketdi. Qolgan ma'lumotni admin bilan suhbatda aytishingiz mumkin — "
    "hozir <b>«✅ Tayyor»</b> tugmasini bosing."
)
TOO_MANY_FILES = "⚠️ Ilova (rasm/fayl/ovoz) soni chegaraga yetdi. <b>«✅ Tayyor»</b> tugmasini bosing."
ATTACHMENT_ONLY = "📎 Faqat ilova yuborilgan (matnsiz)"

BAD_FIRST_NAME = "❗️ Iltimos, ismni to'g'ri kiriting (faqat harflar, 2–40 ta belgi).\n<i>Masalan: Sardor</i>"
BAD_LAST_NAME = "❗️ Iltimos, familiyani to'g'ri kiriting (faqat harflar, 2–40 ta belgi).\n<i>Masalan: Karimov</i>"
BAD_PHONE = (
    "📵 Telefon raqam noto'g'ri.\n"
    "Pastdagi yashil tugmani bosing yoki raqamni shunday yozing:\n"
    "<i>+998 90 123 45 67</i>"
)
BAD_USERNAME = (
    "❗️ Username noto'g'ri. U lotin harflari, raqam va _ belgisidan iborat bo'lib, "
    "kamida 5 ta belgidan tashkil topishi kerak.\n"
    "<i>Masalan: @sardor_dev</i>\n\n"
    "Username'ingiz bo'lmasa — <b>«🚫 Usernamem yo'q»</b> tugmasini bosing."
)
BAD_PRICE = (
    "❗️ Narxni matn ko'rinishida yozing (100 belgigacha).\n"
    "<i>Masalan: 3 000 000 so'm yoki 300$</i>"
)
EXPECT_TEXT = "❗️ Iltimos, so'ralgan ma'lumotni matn ko'rinishida yuboring."
UNSUPPORTED = "🙅 Bu turdagi xabarni qabul qila olmayman. Matn, rasm, fayl yoki ovozli xabar yuboring."


def order_accepted(first_name: str) -> str:
    return (
        f"🎉 <b>Rahmat, {esc(first_name)}!</b>\n\n"
        "✅ Arizangiz qabul qilindi va adminga yuborildi.\n"
        "Admin tez orada siz bilan shu bot orqali bog'lanadi.\n\n"
        "Pastdagi tugmalar yordamida sayt holatini bilishingiz yoki narxni o'zgartirishingiz mumkin 👇"
    )


ADMIN_NOT_CUSTOMER = (
    "ℹ️ Siz hali mijoz sifatida ariza qoldirmagansiz. "
    "Sinab ko'rish uchun <b>«🧪 Mijoz sifatida sinash»</b> tugmasini bosing."
)
CANCELLED = "❌ Bekor qilindi."
CANCELLED_NEW = "❌ Bekor qilindi. Qaytadan boshlash uchun <b>«🚀 Boshlash»</b> tugmasini bosing."
NOT_REGISTERED = (
    "ℹ️ Avval ariza qoldiring: /start buyrug'ini yuboring yoki "
    "<b>«🚀 Boshlash»</b> tugmasini bosing."
)

# ═══════════════ /web ═══════════════
WEB_SENT = "✅ So'rovingiz adminga yuborildi.\nJavob shu yerga keladi — iltimos, biroz kuting ⏳"
WEB_ALREADY_SENT = "⏳ So'rovingiz allaqachon adminga yuborilgan. Javobni kuting."
WEB_UNAVAILABLE = "⚠️ Hozir so'rovni adminga yetkazib bo'lmadi. Iltimos, birozdan so'ng qayta urinib ko'ring."
WEB_READY = "🎉 <b>Saytingiz tayyor!</b>\n\nBatafsil ma'lumot uchun admin siz bilan bog'lanadi."
WEB_NOT_READY = (
    "⏳ <b>Saytingiz hali tayyor emas.</b>\n\n"
    "Ish davom etmoqda. Holatni keyinroq /web orqali yana tekshirib ko'rishingiz mumkin."
)
WEB_ALREADY_ANSWERED = "ℹ️ Bu so'rovga allaqachon javob berilgan."

# ═══════════════ /edit_narx ═══════════════


def edit_price_prompt(current_price: str) -> str:
    return (
        f"💰 <b>Hozirgi narx:</b> {esc(current_price)}\n\n"
        "Yangi narxni yozing.\n"
        "<i>Masalan: 3 500 000 so'm yoki 350$</i>"
    )


PRICE_SAME = "ℹ️ Bu narx allaqachon saqlangan. Boshqa narx kiriting yoki bekor qiling."
PRICE_UPDATED = "✅ Narx yangilandi va adminga yuborildi."

# ═══════════════ Mijoz ↔ admin yozishmasi ═══════════════
ADMIN_MESSAGE_HEADER = "📩 <b>WebMakerUz admini:</b>"
SENT_TO_ADMIN = "✅ Xabaringiz adminga yuborildi."
CANT_DELIVER = "⚠️ Hozir xabarni yetkazib bo'lmadi. Iltimos, keyinroq urinib ko'ring."


def unknown_command(is_admin: bool) -> str:
    text = (
        "❓ Noma'lum buyruq.\n\n"
        "Mavjud buyruqlar:\n"
        "/start — botni boshlash\n"
        "/web — sayt tayyor bo'ldimi?\n"
        "/edit_narx — narxni o'zgartirish"
    )
    if is_admin:
        text += "\n/mijozlar — mijozlar ro'yxati\n/yuklash — web saytni yuklash"
    return text


# ═══════════════ Admin ═══════════════
ADMIN_PANEL = (
    "👑 <b>Admin panel</b>\n\n"
    "Yangi buyurtmalar va mijoz xabarlari shu yerga keladi.\n\n"
    "📋 /mijozlar — barcha mijozlar ro'yxati\n"
    "✍️ Mijozga yozish — xabar boshidagi raqamni bosing (masalan, /1) yoki "
    "«Javob yozish» tugmasidan foydalaning.\n"
    "🌐 /yuklash — tayyor saytning havolasini mijozga yuborish (to'lov so'rovi bilan)\n"
    "🔚 Suhbatni tugatish — «Suhbatni tugatish» tugmasi.\n\n"
    "🧪 Botni mijoz sifatida sinab ko'rish uchun «Mijoz sifatida sinash» tugmasini bosing."
)
ADMIN_HINT = (
    "ℹ️ Mijozga yozish uchun mijoz raqamini bosing (masalan, /1) yoki /mijozlar ro'yxatini oching."
)
CUSTOMER_NOT_FOUND = "❌ Bunday raqamli mijoz topilmadi."
NO_CUSTOMERS = "📭 Hozircha mijozlar yo'q."
CHAT_HINT = (
    "\n\n✍️ <b>Endi yozgan xabaringiz shu mijozga yuboriladi</b> (matn, rasm, fayl, ovoz...).\n"
    "Boshqa mijoz uchun uning raqamini bosing yoki <b>«🔚 Suhbatni tugatish»</b> tugmasini bosing."
)
CHAT_ENDED = "🔚 Suhbat tugatildi."
BLOCKED = "⚠️ Mijoz botni bloklagan yoki chatni o'chirgan — xabar yetib bormadi."
WEB_ANSWER_SENT = "✅ Mijozga yuborildi"
WEB_ANSWER_BLOCKED = "⚠️ Mijoz botni bloklagan — javob yetib bormadi"
WEB_REQUEST_NOT_FOUND = "❌ So'rov topilmadi"


def delivered(customer_id: int) -> str:
    return f"✅ Yuborildi → /{customer_id}"


# ═══════════════ Tizim ═══════════════
TOO_FAST = "⏳ Juda tez yozyapsiz. Iltimos, biroz kuting."
ERROR_GENERIC = "⚠️ Kutilmagan xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
ERROR_ALERT = "⚠️ Xatolik yuz berdi. Qaytadan urinib ko'ring."


# ═══════════════ Sayt yuklash, to'lov va chek ═══════════════
BTN_ADMIN_UPLOAD = "🌐 Web saytni yuklash"
INL_PAID = "✅ Tayyor"
INL_REPAY = "🧾 Chekni qayta yuborish"
INL_APPROVE = "✅ Tasdiqlash"
INL_REJECT = "❌ Rad etish"

UPLOAD_PROMPT = (
    "🌐 <b>Web saytni yuklash</b>\n\n"
    "Saytning havolasini yuboring. Avval mijoz raqami, ketidan havola:\n\n"
    "<code>/5 https://sayt-manzili.uz</code>\n\n"
    "Mijoz raqamlari: /mijozlar"
)
UPLOAD_FORMAT_HINT = (
    "❗️ Format: avval mijoz raqami, ketidan havola.\n"
    "Masalan: <code>/5 https://sayt-manzili.uz</code>"
)
UPLOAD_BAD_LINK = (
    "❗️ Havola noto'g'ri.\n"
    "Masalan: <code>/5 https://sayt-manzili.uz</code>"
)
PAYMENT_NOT_CONFIGURED = (
    "⚠️ <b>Karta raqami kiritilmagan.</b>\n\n"
    "<code>.env</code> faylidagi <code>CARD_NUMBER=</code> qatoriga o'z karta raqamingizni yozing "
    "(masalan: <code>CARD_NUMBER=8600 1234 5678 9012</code>), so'ng botni qayta ishga tushiring."
)


def upload_need_link(customer_id: str) -> str:
    return (
        "❗️ Mijoz raqamidan keyin havolani ham yozing.\n"
        f"Masalan: <code>/{esc(customer_id)} https://sayt-manzili.uz</code>"
    )


SEND_RECEIPT = (
    "🧾 <b>To'lov chekini yuboring</b>\n\n"
    "Chekning rasmini (skrinshot) yoki faylini shu yerga tashlang."
)
RECEIPT_EXPECTED = "❗️ Iltimos, chekni rasm (skrinshot) yoki fayl ko'rinishida yuboring."
RECEIPT_SENT = "✅ <b>Chek adminga yuborildi.</b>\nTo'lov tekshirilgach, sizga xabar beramiz ⏳"
RECEIPT_TOO_MANY = "⏳ Avvalgi cheklaringiz hali ko'rib chiqilmoqda. Iltimos, biroz kuting."
RECEIPT_UNAVAILABLE = "⚠️ Hozir chekni adminga yetkazib bo'lmadi. Iltimos, birozdan so'ng qayta yuboring."
RECEIPT_REJECTED = (
    "❌ <b>Chek tasdiqlanmadi.</b>\n\n"
    "To'lov ko'rinmadi yoki chek noaniq. Iltimos, chekni qayta yuboring yoki admin bilan bog'laning."
)
PAYMENT_NOT_FOUND = "❌ To'lov so'rovi topilmadi."
PAYMENT_ALREADY_PAID = "ℹ️ Bu to'lov allaqachon tasdiqlangan."
PAYMENT_STALE = "ℹ️ Bu to'lov so'rovi eskirgan. Yangi so'rov kelishini kuting."
RECEIPT_ALREADY_DECIDED = "ℹ️ Bu chek allaqachon ko'rib chiqilgan."
RECEIPT_APPROVED_ALERT = "✅ To'lov tasdiqlandi, mijozga yuborildi"
RECEIPT_REJECTED_ALERT = "❌ Rad etildi, mijozga xabar yuborildi"
RECEIPT_NOT_DELIVERED_ALERT = "⚠️ Mijoz botni bloklagan — xabar yetib bormadi"


def payment_approved(link: str) -> str:
    return (
        "✅ <b>To'lov tasdiqlandi!</b> Rahmat 🙏\n\n"
        f"🌐 <b>Saytingiz:</b> {esc(link)}\n\n"
        "Savollaringiz bo'lsa, shu yerga yozing — admin javob beradi."
    )
