"""SQLite (aiosqlite) bilan ishlash: mijozlar, buyurtmalar, /web so'rovlari."""
import asyncio
import logging
from pathlib import Path
from typing import Any

import aiosqlite

from services.misc.formatting import now_str

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,   -- aynan shu raqam /1, /2, /3 ... bo'ladi
    tg_id      INTEGER NOT NULL UNIQUE,
    first_name TEXT    NOT NULL,
    last_name  TEXT    NOT NULL,
    phone      TEXT    NOT NULL,
    username   TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    description TEXT    NOT NULL,
    attachments INTEGER NOT NULL DEFAULT 0,
    price       TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'new',     -- new | ready
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);

CREATE TABLE IF NOT EXISTS web_requests (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id      INTEGER NOT NULL REFERENCES customers(id),
    order_id         INTEGER NOT NULL REFERENCES orders(id),
    answer           TEXT,                          -- NULL (javob yo'q) | yes | no
    answered_by      INTEGER,
    answered_by_name TEXT,
    created_at       TEXT NOT NULL,
    answered_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_web_order ON web_requests(order_id);

-- Admin mijozga yuborgan sayt havolasi (to'lov kutiladi)
CREATE TABLE IF NOT EXISTS deliveries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_id    INTEGER NOT NULL REFERENCES orders(id),
    link        TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'awaiting_payment',  -- awaiting_payment | paid | cancelled
    created_at  TEXT    NOT NULL,
    paid_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_deliveries_customer ON deliveries(customer_id);

-- Mijoz yuborgan to'lov cheklari
CREATE TABLE IF NOT EXISTS receipts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_id     INTEGER NOT NULL REFERENCES deliveries(id),
    status          TEXT    NOT NULL DEFAULT 'pending',       -- pending | approved | rejected
    decided_by      INTEGER,
    decided_by_name TEXT,
    created_at      TEXT    NOT NULL,
    decided_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_receipts_delivery ON receipts(delivery_id);

CREATE TABLE IF NOT EXISTS admin_messages (
    kind       TEXT    NOT NULL,
    ref_id     INTEGER NOT NULL,
    admin_id   INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    PRIMARY KEY (kind, ref_id, admin_id)
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._conn: aiosqlite.Connection | None = None
        self._lock: asyncio.Lock | None = None

    # ───────────── ulanish ─────────────
    async def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()
        logger.info("Ma'lumotlar bazasi tayyor: %s", self.path)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    # ───────────── ichki yordamchilar ─────────────
    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database.init() chaqirilmagan")
        return self._conn

    async def _one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        async with self.conn.execute(sql, params) as cur:
            row = await cur.fetchone()
        return dict(row) if row is not None else None

    async def _all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        async with self.conn.execute(sql, params) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def _write(self, sql: str, params: tuple = ()) -> tuple[int | None, int]:
        """Yozish amali. (lastrowid, rowcount) qaytaradi."""
        assert self._lock is not None
        async with self._lock:
            try:
                async with self.conn.execute(sql, params) as cur:
                    result = (cur.lastrowid, cur.rowcount)
                await self.conn.commit()
            except Exception:
                await self.conn.rollback()
                raise
        return result

    # ───────────── sozlamalar ─────────────
    async def get_setting(self, key: str) -> str | None:
        row = await self._one("SELECT value FROM settings WHERE key = ?", (key,))
        return row["value"] if row else None

    async def set_setting(self, key: str, value: str) -> None:
        await self._write(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    # ───────────── mijozlar ─────────────
    async def get_customer(self, customer_id: int) -> dict[str, Any] | None:
        return await self._one("SELECT * FROM customers WHERE id = ?", (customer_id,))

    async def get_customer_by_tg(self, tg_id: int) -> dict[str, Any] | None:
        return await self._one("SELECT * FROM customers WHERE tg_id = ?", (tg_id,))

    async def count_customers(self) -> int:
        row = await self._one("SELECT COUNT(*) AS n FROM customers")
        return int(row["n"]) if row else 0

    async def list_customers(self, limit: int, offset: int) -> list[dict[str, Any]]:
        return await self._all(
            "SELECT c.*, "
            "(SELECT o.status FROM orders o WHERE o.customer_id = c.id ORDER BY o.id DESC LIMIT 1) "
            "AS last_status, "
            "(SELECT d.status FROM deliveries d WHERE d.customer_id = c.id ORDER BY d.id DESC LIMIT 1) "
            "AS last_delivery "
            "FROM customers c ORDER BY c.id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )

    async def latest_customers(self, limit: int) -> list[dict[str, Any]]:
        return await self._all(
            "SELECT id, first_name, last_name FROM customers ORDER BY id DESC LIMIT ?", (limit,)
        )

    # ───────────── buyurtmalar ─────────────
    async def get_order(self, order_id: int) -> dict[str, Any] | None:
        return await self._one("SELECT * FROM orders WHERE id = ?", (order_id,))

    async def latest_order(self, customer_id: int) -> dict[str, Any] | None:
        return await self._one(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC LIMIT 1", (customer_id,)
        )

    async def count_orders(self, customer_id: int) -> int:
        row = await self._one("SELECT COUNT(*) AS n FROM orders WHERE customer_id = ?", (customer_id,))
        return int(row["n"]) if row else 0

    async def create_customer_with_order(
        self,
        *,
        tg_id: int,
        first_name: str,
        last_name: str,
        phone: str,
        username: str,
        description: str,
        attachments: int,
        price: str,
    ) -> tuple[dict[str, Any], dict[str, Any], bool]:
        """Mijoz (bo'lmasa) va uning buyurtmasini bitta tranzaksiyada yaratadi.

        (mijoz, buyurtma, mijoz_yangi_yaratildimi) qaytaradi."""
        assert self._lock is not None
        ts = now_str()
        async with self._lock:
            try:
                async with self.conn.execute(
                    "SELECT id FROM customers WHERE tg_id = ?", (tg_id,)
                ) as cur:
                    existing = await cur.fetchone()
                created = existing is None
                if created:
                    async with self.conn.execute(
                        "INSERT INTO customers (tg_id, first_name, last_name, phone, username, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (tg_id, first_name, last_name, phone, username, ts),
                    ) as cur:
                        customer_id = cur.lastrowid
                else:
                    customer_id = existing["id"]
                async with self.conn.execute(
                    "INSERT INTO orders (customer_id, description, attachments, price, status, "
                    "created_at, updated_at) VALUES (?, ?, ?, ?, 'new', ?, ?)",
                    (customer_id, description, attachments, price, ts, ts),
                ) as cur:
                    order_id = cur.lastrowid
                await self.conn.commit()
            except Exception:
                await self.conn.rollback()
                raise
        customer = await self.get_customer(customer_id)
        order = await self.get_order(order_id)
        assert customer is not None and order is not None
        return customer, order, created

    async def add_order(
        self, customer_id: int, description: str, attachments: int, price: str
    ) -> dict[str, Any]:
        ts = now_str()
        order_id, _ = await self._write(
            "INSERT INTO orders (customer_id, description, attachments, price, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'new', ?, ?)",
            (customer_id, description, attachments, price, ts, ts),
        )
        order = await self.get_order(order_id)  # type: ignore[arg-type]
        assert order is not None
        return order

    async def update_order_price(self, order_id: int, price: str) -> None:
        await self._write(
            "UPDATE orders SET price = ?, updated_at = ? WHERE id = ?", (price, now_str(), order_id)
        )

    async def set_order_status(self, order_id: int, status: str) -> None:
        await self._write(
            "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?", (status, now_str(), order_id)
        )

    # ───────────── sayt havolasi (yuklash) va to'lov ─────────────
    async def create_delivery(self, customer_id: int, order_id: int, link: str) -> dict[str, Any]:
        """Yangi sayt yuborish yozuvi. Shu buyurtma uchun oldingi to'lanmagan so'rovlar bekor qilinadi."""
        assert self._lock is not None
        async with self._lock:
            try:
                async with self.conn.execute(
                    "UPDATE deliveries SET status = 'cancelled' "
                    "WHERE order_id = ? AND status = 'awaiting_payment'",
                    (order_id,),
                ):
                    pass
                async with self.conn.execute(
                    "INSERT INTO deliveries (customer_id, order_id, link, created_at) VALUES (?, ?, ?, ?)",
                    (customer_id, order_id, link, now_str()),
                ) as cur:
                    delivery_id = cur.lastrowid
                await self.conn.commit()
            except Exception:
                await self.conn.rollback()
                raise
        delivery = await self.get_delivery(delivery_id)  # type: ignore[arg-type]
        assert delivery is not None
        return delivery

    async def get_delivery(self, delivery_id: int) -> dict[str, Any] | None:
        return await self._one("SELECT * FROM deliveries WHERE id = ?", (delivery_id,))

    async def latest_delivery(self, customer_id: int) -> dict[str, Any] | None:
        return await self._one(
            "SELECT * FROM deliveries WHERE customer_id = ? ORDER BY id DESC LIMIT 1", (customer_id,)
        )

    async def mark_delivery_paid(self, delivery_id: int) -> bool:
        """To'langan deb belgilaydi. Faqat birinchi chaqiruvda True (ikki marta tasdiqlashdan himoya)."""
        _, rowcount = await self._write(
            "UPDATE deliveries SET status = 'paid', paid_at = ? WHERE id = ? AND status = 'awaiting_payment'",
            (now_str(), delivery_id),
        )
        return rowcount == 1

    async def create_receipt(self, delivery_id: int) -> int:
        receipt_id, _ = await self._write(
            "INSERT INTO receipts (delivery_id, created_at) VALUES (?, ?)", (delivery_id, now_str())
        )
        return int(receipt_id)  # type: ignore[arg-type]

    async def get_receipt(self, receipt_id: int) -> dict[str, Any] | None:
        return await self._one("SELECT * FROM receipts WHERE id = ?", (receipt_id,))

    async def count_pending_receipts(self, delivery_id: int) -> int:
        row = await self._one(
            "SELECT COUNT(*) AS n FROM receipts WHERE delivery_id = ? AND status = 'pending'", (delivery_id,)
        )
        return int(row["n"]) if row else 0

    async def decide_receipt(self, receipt_id: int, status: str, admin_id: int, admin_name: str) -> bool:
        """Chek bo'yicha qaror yozadi. Allaqachon ko'rib chiqilgan bo'lsa False qaytaradi."""
        _, rowcount = await self._write(
            "UPDATE receipts SET status = ?, decided_by = ?, decided_by_name = ?, decided_at = ? "
            "WHERE id = ? AND status = 'pending'",
            (status, admin_id, admin_name, now_str(), receipt_id),
        )
        return rowcount == 1

    async def delete_receipt(self, receipt_id: int) -> None:
        await self._write("DELETE FROM admin_messages WHERE kind = 'receipt' AND ref_id = ?", (receipt_id,))
        await self._write("DELETE FROM receipts WHERE id = ?", (receipt_id,))

    # ───────────── /web so'rovlari ─────────────
    async def create_web_request(self, customer_id: int, order_id: int) -> int:
        request_id, _ = await self._write(
            "INSERT INTO web_requests (customer_id, order_id, created_at) VALUES (?, ?, ?)",
            (customer_id, order_id, now_str()),
        )
        return int(request_id)  # type: ignore[arg-type]

    async def get_web_request(self, request_id: int) -> dict[str, Any] | None:
        return await self._one("SELECT * FROM web_requests WHERE id = ?", (request_id,))

    async def pending_web_request(self, order_id: int) -> dict[str, Any] | None:
        return await self._one(
            "SELECT * FROM web_requests WHERE order_id = ? AND answer IS NULL ORDER BY id DESC LIMIT 1",
            (order_id,),
        )

    async def answer_web_request(
        self, request_id: int, answer: str, admin_id: int, admin_name: str
    ) -> bool:
        """So'rovga javob yozadi. Allaqachon javob berilgan bo'lsa False qaytaradi."""
        _, rowcount = await self._write(
            "UPDATE web_requests SET answer = ?, answered_by = ?, answered_by_name = ?, answered_at = ? "
            "WHERE id = ? AND answer IS NULL",
            (answer, admin_id, admin_name, now_str(), request_id),
        )
        return rowcount == 1

    async def delete_web_request(self, request_id: int) -> None:
        await self._write("DELETE FROM admin_messages WHERE kind = 'web' AND ref_id = ?", (request_id,))
        await self._write("DELETE FROM web_requests WHERE id = ?", (request_id,))

    # ───────────── adminlardagi xabarlar (tugmalarni sinxronlash uchun) ─────────────
    async def save_admin_message(self, kind: str, ref_id: int, admin_id: int, message_id: int) -> None:
        await self._write(
            "INSERT INTO admin_messages (kind, ref_id, admin_id, message_id) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(kind, ref_id, admin_id) DO UPDATE SET message_id = excluded.message_id",
            (kind, ref_id, admin_id, message_id),
        )

    async def get_admin_messages(self, kind: str, ref_id: int) -> list[dict[str, Any]]:
        return await self._all(
            "SELECT admin_id, message_id FROM admin_messages WHERE kind = ? AND ref_id = ?",
            (kind, ref_id),
        )
