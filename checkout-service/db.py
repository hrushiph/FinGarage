"""Deterministic SQLite database and SQL query counter for checkout-service."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "orders.db"

CUSTOMERS = [
    (1, "Acme Corp", "enterprise", "us-east-1"),
    (2, "Globex Inc", "enterprise", "eu-west-1"),
    (3, "Initech LLC", "growth", "us-west-2"),
    (4, "Umbrella Bio", "enterprise", "us-east-1"),
    (5, "Stark Logistics", "growth", "ap-south-1"),
]


class QueryCountingCursor:
    """Wraps a sqlite3.Cursor to count every executed SQL statement."""

    def __init__(self, cursor: sqlite3.Cursor, counter: list[int]) -> None:
        self._cursor = cursor
        self._counter = counter

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> QueryCountingCursor:
        self._counter[0] += 1
        self._cursor.execute(sql, parameters)
        return self

    def fetchall(self) -> list[Any]:
        return self._cursor.fetchall()

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)


class QueryCountingConnection:
    """Wraps a sqlite3.Connection to track per-request SQL query count."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.counter: list[int] = [0]

    @property
    def query_count(self) -> int:
        return self.counter[0]

    def cursor(self) -> QueryCountingCursor:
        return QueryCountingCursor(self._conn.cursor(), self.counter)

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> QueryCountingCursor:
        cur = self.cursor()
        return cur.execute(sql, parameters)

    def close(self) -> None:
        self._conn.close()


def init_db(db_path: Path = DB_PATH) -> None:
    """Create and deterministically seed the orders database (100 orders)."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS orders")
    cur.execute("DROP TABLE IF EXISTS customers")

    cur.execute(
        """
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            tier TEXT NOT NULL,
            region TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            amount_cents INTEGER NOT NULL,
            status TEXT NOT NULL,
            sku TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
        """
    )

    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", CUSTOMERS)

    orders_data = []
    for i in range(1, 101):
        cust_id = ((i - 1) % len(CUSTOMERS)) + 1
        # Deterministic amounts and statuses so Golden Accuracy checks are exact
        amount_cents = (i * 137 + 4500) % 25000 + 2500
        if i in (14, 42, 77, 91):
            status = "refunded"
            amount_cents = 18500
        elif i in (23, 58):
            status = "payment_retry"
        else:
            status = "completed"
        sku = f"SKU-AI-{(i % 7) + 1:02d}"
        orders_data.append((i, cust_id, amount_cents, status, sku, f"2026-11-03T10:{i % 60:02d}:00Z"))

    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", orders_data)
    conn.commit()
    conn.close()


def open_counted_connection(db_path: Path = DB_PATH) -> QueryCountingConnection:
    """Open a SQLite connection wrapped with a per-request statement counter."""
    if not db_path.exists():
        init_db(db_path)
    raw = sqlite3.connect(db_path)
    raw.row_factory = sqlite3.Row
    return QueryCountingConnection(raw)

