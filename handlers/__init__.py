"""Barcha routerlarni bitta asosiy routerga yig'ish. Tartib MUHIM: birinchi mos kelgan handler ishlaydi."""
from aiogram import Router

from .admins.backup import router as admin_backup_router
from .admins.panel import router as admin_panel_router
from .admins.payments import router as admin_payments_router
from .admins.reply import router as admin_reply_router
from .admins.upload import router as admin_upload_router
from .admins.web_answer import router as admin_web_router
from .errors import router as errors_router
from .users.echo import router as echo_router
from .users.edit_narx import router as edit_narx_router
from .users.form import router as form_router
from .users.payment import router as payment_router
from .users.start import router as start_router
from .users.web import router as web_router

router = Router(name="main")

router.include_router(errors_router)

# Adminlar (avval tekshiriladi)
router.include_router(admin_panel_router)
router.include_router(admin_backup_router)
router.include_router(admin_upload_router)  # "/5 havola" /N dan OLDIN tekshirilishi shart
router.include_router(admin_reply_router)
router.include_router(admin_web_router)
router.include_router(admin_payments_router)

# Foydalanuvchilar: buyruqlar -> forma bosqichlari -> umumiy (echo / noma'lum buyruq)
router.include_router(start_router)
router.include_router(web_router)
router.include_router(edit_narx_router)
router.include_router(payment_router)
router.include_router(form_router)
router.include_router(echo_router)

__all__ = ["router"]
