# 🌐 WebMakerUz Bot

Web saytlarga buyurtma yig'adigan Telegram bot. **aiogram 3.31 · Python 3.14 · SQLite**

Mijoz botga kiradi → rasm va "biz sizga web saytlarni yaratib beramiz" matni chiqadi → ism, familiya,
telefon, username, sayt haqida ma'lumot va narxni qoldiradi → hammasi **adminlarga** boradi.
Admin mijozga bot orqali javob yozadi.

---

## 🚀 Ishga tushirish (Windows)

Papka ichida terminal oching (PowerShell, CMD yoki PyCharm Terminal) va ketma-ket yozing:

```bat
py -3.14 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Konsolda `Bot ishga tushdi: @...` yozuvi chiqsa — bot ishlayapti. To'xtatish: `Ctrl + C`.

**PyCharm:** `File → Open` bilan shu papkani oching → `Settings → Python Interpreter → Add Interpreter →
Existing` va `.venv\Scripts\python.exe` ni tanlang → `main.py` ni Run qiling.

**Linux / macOS:**
```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python main.py
```

> Eski loyihadan olingan `.venv` papkasini ishlatmang (u boshqa Python versiyasi uchun) — yangisini yarating.

---

## ⚙️ Sozlamalar — `.env` fayli

```env
BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMINS=11111111,22222222
CARD_NUMBER=8600 1234 5678 9012
CARD_OWNER=O S
SEND_LINK_BEFORE_PAYMENT=false
```

* `BOT_TOKEN` — @BotFather bergan token
* `ADMINS` — adminlarning Telegram ID raqamlari (vergul bilan)
* `CARD_NUMBER` — **o'zingizning karta raqamingiz** (to'lov uchun mijozga ko'rsatiladi; bo'sh joy yoki tire bilan yozsangiz ham bo'ladi).
  Bo'sh qolsa, «Web saytni yuklash» ishlamaydi va bot buni eslatadi.
* `CARD_OWNER` — karta egasi (karta raqamidan keyin chiqadi, masalan `O S`)
* `SEND_LINK_BEFORE_PAYMENT` — `false` (standart): sayt havolasi mijozga **to'lov tasdiqlangandan keyin** yuboriladi.
  `true`: havola to'lov so'rovi bilan birga darrov yuboriladi.

`.env` ni o'zgartirgach botni qayta ishga tushiring.

🔒 `.env` faylini hech kimga bermang va GitHub'ga yuklamang (`.gitignore` da turibdi).
Token begona odamga ko'rinib qolgan bo'lsa: @BotFather → `/mybots` → botni tanlang → `API Token` → `Revoke current token`,
keyin yangi tokenni `.env` ga yozing.

---

## ⚠️ Birinchi ishga tushirishdan oldin (muhim)

1. **Ikkala admin ham botga kirib `/start` bosishi shart.** Aks holda Telegram botga admin bilan
   birinchi bo'lib yozishga ruxsat bermaydi va buyurtmalar adminga yetib bormaydi.
   (Konsolda `Admin ... botga hali /start bosmagan` degan ogohlantirish chiqsa — shu sabab.)
2. **`.env` faylida `CARD_NUMBER=` ga o'z karta raqamingizni yozing** (pastda "Sayt topshirish va to'lov" bo'limiga qarang).
3. **Bot sahifasidagi rasm** (mijoz botni ochganda, START tugmasidan oldin ko'rinadigan rasm)
   Bot API orqali o'rnatilmaydi — uni @BotFather orqali qo'lda qo'yasiz:

   `@BotFather → /mybots → botingiz → Edit Bot → Edit Description Picture` va
   **`assets/description_pic.jpg`** faylini yuboring (16:9 ko'rinishga tayyorlab qo'yilgan).
   Shu sahifadagi **matn** (tavsif) esa bot ishga tushganda avtomatik o'rnatiladi.

   `/start` bosilgandan keyin esa bot rasmni (`assets/welcome.jpg`) o'zi ham yuboradi.

---

## 📋 Buyruqlar

| Buyruq | Kim uchun | Nima qiladi |
|---|---|---|
| `/start` | hamma | rasm + salom, ro'yxatdan o'tish (ism → familiya → telefon → username → sayt haqida → narx) |
| `/web` | mijoz | adminga **«/N — Sayt tayyor bo'ldimi?»** + `✅ Ha` / `❌ Yo'q` tugmalari yuboradi; admin bosgan javob mijozga boradi |
| `/edit_narx` | mijoz | narxni o'zgartirish; o'zgarish (eski → yangi) adminga boradi |
| `/cancel` | hamma | joriy amalni bekor qilish |
| `/mijozlar` | admin | barcha mijozlar ro'yxati (sahifalangan) |
| `/1`, `/2`, `/3` … | admin | shu raqamli mijozga xabar yozish rejimi |
| `/yuklash` | admin | `🌐 Web saytni yuklash` tugmasi bilan bir xil (pastga qarang) |

* Har bir mijoz ro'yxatdan o'tganda **/1, /2, /3 …** raqamini oladi. Adminga keladigan har bir xabar shu raqam bilan boshlanadi
  (masalan `/5 — Yangi buyurtma`), raqamni bosish — o'sha mijoz bilan yozishmani ochadi.
* Mijoz raqamlari va telefon raqamlari **faqat adminlarga** ko'rinadi (buyruqlar menyusida ham: "/" bosilganda
  adminlarda `/1`, `/2` … chiqadi, oddiy mijozlarda faqat `/start`, `/web`, `/edit_narx`).
  Menyuda oxirgi ~96 ta mijoz ko'rinadi, qolganlari `/mijozlar` orqali ochiladi.
* Admin mijozga matn, rasm, fayl, ovozli xabar yubora oladi. Chiqish: `🔚 Suhbatni tugatish`.
* Mijoz "sayt haqida" bosqichida bir nechta xabar, rasm, fayl va ovoz yuborishi mumkin — `✅ Tayyor` bosilgach hammasi adminga ketadi.
* Ro'yxatdan o'tgan mijozning erkin yozgan xabarlari ham adminlarga `/N` sarlavhasi va `✍️ Javob yozish` tugmasi bilan boradi.
* `🧪 Mijoz sifatida sinash` (adminda) — botni oddiy mijoz kabi o'zingiz sinab ko'rish uchun.
* Tugmalar rangli: 🟢 yashil (tasdiqlash), 🔴 qizil (bekor qilish), 🔵 ko'k (asosiy amallar).
  Ranglar Telegram'ning yangi versiyalarida ko'rinadi — ilovani yangilab qo'ying.

---

## 🌐 Sayt topshirish va to'lov (faqat adminlar uchun)

1. Admin **`🌐 Web saytni yuklash`** tugmasini bosadi (yoki `/yuklash`) → bot saytning havolasini so'raydi.
2. Admin avval **mijoz raqamini**, ketidan **havolani** yuboradi:

   ```
   /5 https://sayt-manzili.uz
   ```
   (Tugmani bosmasdan shu ko'rinishda yozsa ham ishlaydi. Mijoz raqamlarini `/mijozlar` dan ko'rasiz.)
3. Mijozga **to'lov so'rovi** boradi: karta raqami (bosib nusxalash mumkin) + karta egasi + narx va tagida **`✅ Tayyor`** tugmasi.
   Sayt havolasi hali ko'rsatilmaydi.
4. Mijoz to'lovdan so'ng `✅ Tayyor` ni bosadi → bot **«chekni yuboring»** deydi → mijoz chekni (rasm/skrinshot yoki fayl) tashlaydi →
   chek **to'g'ridan-to'g'ri adminlarga** boradi: `/5 — 🧾 To'lov cheki` + `✅ Tasdiqlash` / `❌ Rad etish` tugmalari.
5. Admin **tasdiqlasa** — mijozga sayt havolasi yuboriladi (buyurtma 💰 belgisi bilan `/mijozlar` da ko'rinadi).
   **Rad etsa** — mijozga «chek tasdiqlanmadi» va `🧾 Chekni qayta yuborish` tugmasi boradi.

* Ikki admin bo'lsa: birinchi bosgan javob hisobga olinadi, ikkinchisining tugmalari o'chadi, mijozga xabar ikki marta ketmaydi.
* Admin xuddi shu mijoz uchun yangi havola yuborsa, eski to'lov so'rovi bekor bo'ladi.
* Havola `sayt.uz` ko'rinishida yozilsa, boshiga `https://` avtomatik qo'shiladi.

---

## 🗂 Loyiha tuzilmasi

```
main.py                  — ishga tushirish
config/config.py         — .env dan sozlamalar
handlers/
  users/                 — start, forma (FSM), web, edit_narx, payment (to'lov cheki), echo
  admins/                — mijozlar ro'yxati, /N yozishma, Ha/Yo'q javoblari, sayt yuklash (upload.py), chek tasdiqlash (payments.py)
  errors.py              — xatoliklarni ushlash
keyboards/               — rangli tugmalar (default = oddiy, inline = xabar ostidagi)
states/                  — FSM holatlari
filters/  middlewares/   — admin filtri, spamdan himoya
services/
  db_api/                — SQLite (mijozlar, buyurtmalar, /web so'rovlari)
  misc/texts.py          — BARCHA matnlar shu faylda (tahrirlash oson)
  notify_admins.py, set_bot_commands.py, welcome.py, ...
assets/                  — welcome.jpg (botdagi rasm), description_pic.jpg (BotFather uchun)
data/webmaker.db         — ma'lumotlar bazasi (avtomatik yaratiladi; zaxira nusxa uchun shu faylni saqlang)
```

Matnlarni o'zgartirmoqchi bo'lsangiz — `services/misc/texts.py`; botdagi rasmni almashtirmoqchi bo'lsangiz —
`assets/welcome.jpg` ni (shu nom bilan) almashtirib, botni qayta ishga tushiring: bot o'zgarishni o'zi payqaydi.
