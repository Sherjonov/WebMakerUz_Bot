"""Foydalanuvchi kiritgan ma'lumotlarni tekshirish va tozalash."""
import re
from urllib.parse import urlsplit

from config.config import MAX_PRICE_CHARS

# Harflar (lotin/kirill), bo'sh joy, defis va turli apostroflar: O'ktam, G'ayrat, Anna-Maria
_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '’ʻʼ‘`´-]+[^\W\d_]+)*$")
_USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,31}$")
_TME_PREFIX_RE = re.compile(r"^(?:https?://)?(?:www\.)?(?:t|telegram)\.me/", re.IGNORECASE)


def clean_name(raw: str | None) -> str | None:
    """Ism/familiyani tekshiradi va chiroyli ko'rinishga keltiradi. Noto'g'ri bo'lsa None."""
    if not raw:
        return None
    value = " ".join(raw.split())
    if not 2 <= len(value) <= 40 or not _NAME_RE.fullmatch(value):
        return None
    words = []
    for word in value.split(" "):
        if word.isupper() or word.islower():
            word = word[:1].upper() + word[1:].lower()
        words.append(word)
    return " ".join(words)


def normalize_phone(raw: str | None, *, from_contact: bool = False) -> str | None:
    """Telefon raqamni +998901234567 ko'rinishiga keltiradi. Noto'g'ri bo'lsa None."""
    if not raw:
        return None
    raw = raw.strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None

    if digits.startswith("998") and len(digits) != 12 and (from_contact or raw.startswith("+")):
        return None  # +998 bilan boshlangan, lekin uzunligi noto'g'ri

    if from_contact or raw.startswith("+"):
        return "+" + digits if 8 <= len(digits) <= 15 else None

    if len(digits) == 9:                                   # 901234567
        return "+998" + digits
    if len(digits) == 10 and digits.startswith("0"):       # 0901234567
        return "+998" + digits[1:]
    if len(digits) == 12 and digits.startswith("998"):     # 998901234567
        return "+" + digits
    return None


def normalize_username(raw: str | None) -> str | None:
    """@username, username yoki t.me/username ni '@username' ko'rinishiga keltiradi."""
    if not raw:
        return None
    value = _TME_PREFIX_RE.sub("", raw.strip()).lstrip("@").strip().rstrip("/")
    return "@" + value if _USERNAME_RE.fullmatch(value) else None


def clean_price(raw: str | None) -> str | None:
    """Narx matnini tozalaydi (erkin shakl: '3 000 000 so'm', '300$' ...)."""
    if not raw:
        return None
    value = " ".join(raw.split())
    if not value or len(value) > MAX_PRICE_CHARS or value.startswith("/"):
        return None
    return value


def normalize_link(raw: str | None) -> str | None:
    """Sayt havolasini tekshiradi. 'sayt.uz' deb yozilsa boshiga https:// qo'shadi. Noto'g'ri bo'lsa None."""
    if not raw:
        return None
    value = raw.strip()
    if not value or len(value) > 300 or any(ch.isspace() for ch in value):
        return None
    if not re.match(r"^[A-Za-z][A-Za-z0-9+.\-]*://", value):
        value = "https://" + value
    try:
        parts = urlsplit(value)
        host = parts.hostname or ""
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or not host:
        return None
    if "." not in host and host != "localhost":
        return None
    return value
