"""Render (va shunga o'xshash hostinglar) uchun: oddiy HTTP server + botni uyg'oq tutish.

Muammo: Render "Web Service" dastur port ochishini talab qiladi. Bot esa port ochmaydi (u Telegramga o'zi
ulanadi), shuning uchun Render "No open ports detected" deb 6 daqiqadan so'ng xizmatni to'xtatardi (Timed Out).
Yechim: PORT berilgan bo'lsa, kichik HTTP server ochamiz (/health). Bepul tarifda xizmat 15 daqiqa so'rovsiz
qolsa uxlab qoladi — shuning uchun o'zimizga vaqti-vaqti bilan so'rov yuborib turamiz."""
import asyncio
import logging

import aiohttp
from aiohttp import web

from config import config as cfg

logger = logging.getLogger(__name__)


async def _ok(request: web.Request) -> web.Response:
    return web.Response(text="WebMakerUz Bot ishlayapti ✅")


async def start_health_server(port: int | None = None, host: str = "0.0.0.0") -> web.AppRunner | None:
    """PORT berilgan bo'lsa HTTP serverni ishga tushiradi. PORT yo'q (masalan, kompyuterda) bo'lsa — hech narsa qilmaydi."""
    port = cfg.PORT if port is None else port
    if not port:
        return None

    app = web.Application()
    app.router.add_get("/", _ok)
    app.router.add_get("/health", _ok)
    app.router.add_get("/healthz", _ok)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    try:
        await web.TCPSite(runner, host, port).start()
    except OSError as e:
        logger.error("Health server %s:%s portini ocholmadi: %s", host, port, e)
        await runner.cleanup()
        return None
    logger.info("Health server ishga tushdi: %s:%s (Render port tekshiruvi uchun)", host, port)
    return runner


async def keep_alive_loop(url: str, interval: float, first_delay: float = 30.0) -> None:
    """Xizmat uxlab qolmasligi uchun `url` ga vaqti-vaqti bilan GET so'rov yuboradi."""
    timeout = aiohttp.ClientTimeout(total=30)
    delay = first_delay
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while True:
            await asyncio.sleep(delay)
            delay = interval
            try:
                async with session.get(url) as response:
                    logger.info("Keep-alive: %s -> %s", url, response.status)
            except (aiohttp.ClientError, TimeoutError) as e:
                logger.warning("Keep-alive so'rovi muvaffaqiyatsiz (%s): %s", url, e)


def start_keep_alive() -> asyncio.Task | None:
    """Render muhitida (yoki KEEP_ALIVE_URL berilsa) fon vazifasini ishga tushiradi."""
    if not (cfg.KEEP_ALIVE_ENABLED and cfg.KEEP_ALIVE_URL):
        return None
    url = f"{cfg.KEEP_ALIVE_URL}/health"
    logger.info("Keep-alive yoqildi: har %s soniyada %s", cfg.KEEP_ALIVE_INTERVAL, url)
    return asyncio.create_task(keep_alive_loop(url, cfg.KEEP_ALIVE_INTERVAL), name="keep-alive")
