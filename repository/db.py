"""
Database initialisation and session helpers.

Uses plain sqlite3 — no ORM needed for this scale.
All tables match the AgNet / CIS data models from the spec.
"""

import sqlite3
import config

_connection = None


def get_connection():
    """Return a module-level connection (reused across requests)."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(
            config.DATABASE_PATH,
            check_same_thread=False,
        )
        _connection.row_factory = sqlite3.Row
        _init_tables(_connection)
    return _connection


def init_db(db_path=None):
    """Initialise (or re-initialise) the database — useful for tests."""
    global _connection
    path = db_path or config.DATABASE_PATH
    _connection = sqlite3.connect(path, check_same_thread=False)
    _connection.row_factory = sqlite3.Row
    _init_tables(_connection)
    return _connection


def _init_tables(conn):
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS vendors (
            vendor_id   TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            type        TEXT,
            reg_state   TEXT DEFAULT 'New',
            order_count INTEGER DEFAULT 0,
            last_order  TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS categories (
            category_id         TEXT PRIMARY KEY,
            parent_category_id  TEXT,
            category_name       TEXT NOT NULL,
            level               INTEGER NOT NULL,
            created_at          TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id   TEXT PRIMARY KEY,
            vendor_id    TEXT,
            category_id  TEXT,
            product_name TEXT NOT NULL,
            unit         TEXT NOT NULL,
            created_at   TEXT DEFAULT (datetime('now')),
            updated_at   TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (vendor_id)   REFERENCES vendors(vendor_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        );

        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id   TEXT PRIMARY KEY,
            vendor_id     TEXT NOT NULL,
            shipment_date TEXT NOT NULL,
            cis_status    TEXT DEFAULT 'pending',
            created_at    TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        );

        CREATE TABLE IF NOT EXISTS shipment_lots (
            lot_id             TEXT PRIMARY KEY,
            shipment_id        TEXT NOT NULL,
            product_id         TEXT NOT NULL,
            quantity_on_hand   REAL NOT NULL,
            unit               TEXT NOT NULL,
            last_restocked     TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
            FOREIGN KEY (product_id)  REFERENCES products(product_id)
        );

        CREATE TABLE IF NOT EXISTS procurement_orders (
            order_id        TEXT PRIMARY KEY,
            vendor_id       TEXT NOT NULL,
            agnet_order_id  TEXT,
            status          TEXT DEFAULT 'pending',
            total_items     INTEGER DEFAULT 0,
            payload_json    TEXT,
            result_json     TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            item_id          TEXT PRIMARY KEY,
            order_id         TEXT NOT NULL,
            product_id       TEXT NOT NULL,
            quantity_ordered INTEGER NOT NULL,
            unit             TEXT NOT NULL,
            FOREIGN KEY (order_id)   REFERENCES procurement_orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
    """)
    conn.commit()


def close_db():
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
