"""Bot sozlamalari. Qiymatlar .env faylidan o'qiladi."""
import os
import re
from datetime import timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# utf-8-sig: Windows "Блокнот" saqlagan BOM belgisi bo'lsa ham xato bermaydi
load_dotenv(BASE_DIR / ".env", encoding="utf-8-sig")


def _flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "ha", "on"}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _parse_admins(raw: str) -> list[int]:
    ids: list[int] = []
    for part in raw.replace(";", ",").replace(" ", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise SystemExit(
                f".env faylidagi ADMINS noto'g'ri: '{part}'. "
                "Faqat raqamlar bo'lsin, vergul bilan ajrating. Masalan: ADMINS=111,222"
            )
        ids.append(int(part))
    return list(dict.fromkeys(ids))  # takrorlarni olib tashlaydi, tartib saqlanadi


BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMINS: list[int] = _parse_admins(os.getenv("ADMINS", ""))

if not BOT_TOKEN:
    raise SystemExit(".env faylida BOT_TOKEN topilmadi. Namuna uchun .env.example ga qarang.")
if not ADMINS:
    raise SystemExit(".env faylida ADMINS topilmadi. Namuna uchun .env.example ga qarang.")

DB_PATH = Path(os.getenv("DB_PATH") or BASE_DIR / "data" / "webmaker.db")
ASSETS_DIR = BASE_DIR / "assets"
WELCOME_PHOTO = ASSETS_DIR / "welcome.jpg"

# O'zbekiston vaqti: UTC+5 (yozgi/qishki vaqtga o'tilmaydi)
TASHKENT_TZ = timezone(timedelta(hours=5), "UZT")

# ---- To'lov (karta) sozlamalari: .env faylidan ----
CARD_NUMBER: str = re.sub(r"\D", "", os.getenv("CARD_NUMBER", ""))  # faqat raqamlar saqlanadi
CARD_OWNER: str = os.getenv("CARD_OWNER", "").strip()
# True bo'lsa sayt havolasi mijozga to'lovdan OLDIN (to'lov so'rovi bilan birga) yuboriladi
SEND_LINK_BEFORE_PAYMENT: bool = os.getenv("SEND_LINK_BEFORE_PAYMENT", "false").strip().lower() in {
    "1", "true", "yes", "ha",
}


def payment_configured() -> bool:
    """Karta raqami .env da to'g'ri kiritilganmi (12-19 ta raqam)."""
    return 12 <= len(CARD_NUMBER) <= 19


# ---- Hosting (Render va shunga o'xshash xizmatlar) ----
ON_RENDER: bool = bool(os.getenv("RENDER"))
# Render "Web Service" ga PORT beradi va bot shu portni OCHISHI shart (aks holda "No open ports detected" -> "Timed Out")
PORT: int = _int_env("PORT", 0)
# Bepul tarifda xizmat 15 daqiqa so'rovsiz qolsa uxlab qoladi -> bot o'ziga vaqti-vaqti bilan so'rov yuboradi
KEEP_ALIVE_ENABLED: bool = _flag("KEEP_ALIVE", True)
KEEP_ALIVE_URL: str = (os.getenv("KEEP_ALIVE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").strip().rstrip("/")
KEEP_ALIVE_INTERVAL: int = max(60, _int_env("KEEP_ALIVE_INTERVAL", 600))  # soniya
# Ma'lumotlar bazasi zaxirasi (Render bepul tarifida fayllar o'chib ketadi)
BACKUP_ENABLED: bool = _flag("BACKUP", True)
BACKUP_INTERVAL_MINUTES: int = max(5, _int_env("BACKUP_INTERVAL_MINUTES", 15))

# ---- Cheklovlar ----
MAX_DESCRIPTION_CHARS = 6000   # sayt haqida yozilgan matnning umumiy uzunligi
MAX_ATTACHMENTS = 10           # bitta buyurtmaga qo'shiladigan rasm/fayl/ovoz soni
MAX_PRICE_CHARS = 100          # narx maydonining uzunligi
WEB_REQUEST_COOLDOWN = 120     # /web ni qayta yuborish oralig'i (soniya)
CUSTOMERS_PER_PAGE = 15        # /mijozlar ro'yxatida bir sahifadagi mijozlar
MAX_PENDING_RECEIPTS = 3       # bitta to'lov uchun ko'rib chiqilmagan cheklar soni
