"""TripWatch AI — camada de persistência (SQLite, sem dependências externas)."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from catalog import REPOS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("TRIPWATCH_DB", os.path.join(BASE_DIR, "data", "tripwatch.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS watches (
    id              TEXT PRIMARY KEY,
    kind            TEXT NOT NULL CHECK (kind IN ('flight','hotel')),
    title           TEXT NOT NULL,
    origin          TEXT,
    destination     TEXT,
    depart_date     TEXT,
    return_date     TEXT,
    hotel_name      TEXT,
    city            TEXT,
    checkin         TEXT,
    checkout        TEXT,
    guests          INTEGER DEFAULT 1,
    rooms           INTEGER DEFAULT 1,
    cabin           TEXT DEFAULT 'economy',
    target_price    REAL,
    currency        TEXT DEFAULT 'BRL',
    base_price      REAL NOT NULL,
    interval_minutes INTEGER DEFAULT 180,
    active          INTEGER DEFAULT 1,
    last_checked_at TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_id   TEXT NOT NULL REFERENCES watches(id) ON DELETE CASCADE,
    price      REAL NOT NULL,
    currency   TEXT NOT NULL,
    provider   TEXT NOT NULL,
    found_at   TEXT NOT NULL,
    meta       TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id         TEXT PRIMARY KEY,
    watch_id   TEXT NOT NULL REFERENCES watches(id) ON DELETE CASCADE,
    kind       TEXT NOT NULL,
    message    TEXT NOT NULL,
    price      REAL,
    created_at TEXT NOT NULL,
    read_at    TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    status      TEXT NOT NULL,
    checked     INTEGER DEFAULT 0,
    alerts      INTEGER DEFAULT 0,
    log         TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repos (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    url         TEXT NOT NULL UNIQUE,
    description TEXT,
    category    TEXT,
    language    TEXT,
    license     TEXT,
    stars       INTEGER DEFAULT 0,
    mcp_url     TEXT,
    install_cmd TEXT,
    best_for    TEXT,
    added_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_watch ON snapshots(watch_id, found_at);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);
"""

DEFAULT_SETTINGS = {
    "check_interval_minutes": "180",
    "currency": "BRL",
    "webhook_url": "",
    "alert_drop_pct": "5",
    "llm_provider": "auto",
    "llm_model": "",
    "agent_name": "TripWatch Agent",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str = "w") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def query(sql: str, params: Iterable[Any] = ()) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(r) for r in rows]


def query_one(sql: str, params: Iterable[Any] = ()) -> dict | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    with connect() as conn:
        cur = conn.execute(sql, tuple(params))
        conn.commit()
        return cur.lastrowid


def get_setting(key: str, default: str | None = None) -> str:
    row = query_one("SELECT value FROM settings WHERE key = ?", (key,))
    if row:
        return row["value"]
    return DEFAULT_SETTINGS.get(key, default) if default is None else default


def set_setting(key: str, value: str) -> None:
    execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )


def all_settings() -> dict[str, str]:
    stored = {r["key"]: r["value"] for r in query("SELECT key, value FROM settings")}
    merged = dict(DEFAULT_SETTINGS)
    merged.update(stored)
    return merged


# --------------------------------------------------------------------------- #
# Modelo de preço do provedor demo
# --------------------------------------------------------------------------- #

def demo_price(watch: dict, when: datetime | None = None) -> tuple[float, dict]:
    """Gera um preço determinístico por janela de 3h (parece um mercado real)."""
    when = when or datetime.now(timezone.utc)
    bucket = int(when.timestamp() // (3 * 3600))
    seed = int(hashlib.sha256(f"{watch['id']}:{bucket}".encode()).hexdigest()[:12], 16)
    rng = random.Random(seed)
    base = float(watch["base_price"])
    day = when.timestamp() / 86400
    phase = (int(watch["id"][-4:], 16) % 17) if watch["id"][-4:].isalnum() else 3
    wave = math.sin(day / 3.4 + phase) * 0.055
    noise = rng.uniform(-0.032, 0.032)
    promo = -0.14 if rng.random() < 0.055 else 0.0
    spike = 0.09 if rng.random() < 0.035 else 0.0
    factor = 1 + wave + noise + promo + spike
    if watch["kind"] == "hotel":
        factor = 1 + (factor - 1) * 0.55
    price = round(base * factor, 2)
    return max(price, base * 0.55), {
        "mode": "demo",
        "note": "Simulador determinístico — configure SERPAPI_KEY para preços reais.",
    }


# --------------------------------------------------------------------------- #
# Watchlist
# --------------------------------------------------------------------------- #

def list_watches(kind: str | None = None) -> list[dict]:
    if kind:
        rows = query("SELECT * FROM watches WHERE kind = ? ORDER BY created_at DESC", (kind,))
    else:
        rows = query("SELECT * FROM watches ORDER BY created_at DESC")
    for row in rows:
        row["active"] = bool(row["active"])
        row["snapshots"] = query(
            "SELECT price, currency, provider, found_at, meta FROM snapshots "
            "WHERE watch_id = ? ORDER BY found_at ASC",
            (row["id"],),
        )
        row["last_price"] = row["snapshots"][-1]["price"] if row["snapshots"] else None
        row["alerts_count"] = query_one(
            "SELECT COUNT(*) AS c FROM alerts WHERE watch_id = ? AND read_at IS NULL",
            (row["id"],),
        )["c"]
    return rows


def get_watch(watch_id: str) -> dict | None:
    rows = query("SELECT * FROM watches WHERE id = ?", (watch_id,))
    return rows[0] if rows else None


def create_watch(data: dict) -> dict:
    kind = data.get("kind", "flight")
    watch = {
        "id": new_id("w"),
        "kind": kind,
        "title": data.get("title") or _default_title(kind, data),
        "origin": data.get("origin"),
        "destination": data.get("destination"),
        "depart_date": data.get("depart_date"),
        "return_date": data.get("return_date"),
        "hotel_name": data.get("hotel_name"),
        "city": data.get("city"),
        "checkin": data.get("checkin"),
        "checkout": data.get("checkout"),
        "guests": int(data.get("guests") or 1),
        "rooms": int(data.get("rooms") or 1),
        "cabin": data.get("cabin") or "economy",
        "target_price": float(data["target_price"]) if data.get("target_price") else None,
        "currency": data.get("currency") or get_setting("currency", "BRL"),
        "base_price": float(data["base_price"]),
        "interval_minutes": int(data.get("interval_minutes") or get_setting("check_interval_minutes", "180")),
        "active": 1,
        "last_checked_at": None,
        "created_at": now_iso(),
    }
    cols = ", ".join(watch.keys())
    placeholders = ", ".join("?" for _ in watch)
    with connect() as conn:
        conn.execute(f"INSERT INTO watches ({cols}) VALUES ({placeholders})", tuple(watch.values()))
        conn.commit()
    return get_watch(watch["id"])


def _default_title(kind: str, data: dict) -> str:
    if kind == "flight":
        return f"{data.get('origin', '?')} → {data.get('destination', '?')}"
    return data.get("hotel_name") or data.get("city") or "Hotel"


def update_watch(watch_id: str, patch: dict) -> dict | None:
    allowed = {
        "title", "target_price", "interval_minutes", "active", "cabin", "guests",
        "rooms", "depart_date", "return_date", "checkin", "checkout",
    }
    fields = {k: v for k, v in patch.items() if k in allowed}
    if not fields:
        return get_watch(watch_id)
    if "active" in fields:
        fields["active"] = 1 if fields["active"] else 0
    if "target_price" in fields:
        fields["target_price"] = float(fields["target_price"]) if fields["target_price"] not in (None, "") else None
    if "interval_minutes" in fields:
        fields["interval_minutes"] = max(15, int(fields["interval_minutes"]))
    assignments = ", ".join(f"{k} = ?" for k in fields)
    with connect() as conn:
        conn.execute(f"UPDATE watches SET {assignments} WHERE id = ?", (*fields.values(), watch_id))
        conn.commit()
    return get_watch(watch_id)


def delete_watch(watch_id: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM alerts WHERE watch_id = ?", (watch_id,))
        conn.execute("DELETE FROM snapshots WHERE watch_id = ?", (watch_id,))
        conn.execute("DELETE FROM watches WHERE id = ?", (watch_id,))
        conn.commit()


def add_snapshot(watch_id: str, price: float, provider: str, meta: dict | None = None) -> dict:
    row = {
        "id": execute(
            "INSERT INTO snapshots(watch_id, price, currency, provider, found_at, meta) VALUES(?,?,?,?,?,?)",
            (
                watch_id,
                price,
                get_watch(watch_id)["currency"],
                provider,
                now_iso(),
                json.dumps(meta or {}, ensure_ascii=False),
            ),
        ),
        "watch_id": watch_id,
        "price": price,
        "provider": provider,
        "found_at": now_iso(),
    }
    return row


def add_alert(watch_id: str, kind: str, message: str, price: float | None = None) -> dict:
    alert = {
        "id": new_id("a"),
        "watch_id": watch_id,
        "kind": kind,
        "message": message,
        "price": price,
        "created_at": now_iso(),
        "read_at": None,
    }
    with connect() as conn:
        conn.execute(
            "INSERT INTO alerts(id, watch_id, kind, message, price, created_at, read_at) VALUES(?,?,?,?,?,?,NULL)",
            (
                alert["id"], alert["watch_id"], alert["kind"], alert["message"],
                alert["price"], alert["created_at"],
            ),
        )
        conn.commit()
    return alert


def list_alerts(limit: int = 50, unread_only: bool = False) -> list[dict]:
    sql = "SELECT a.*, w.title, w.kind AS watch_kind FROM alerts a JOIN watches w ON w.id = a.watch_id"
    if unread_only:
        sql += " WHERE a.read_at IS NULL"
    sql += " ORDER BY a.created_at DESC LIMIT ?"
    return query(sql, (limit,))


def mark_alerts_read(alert_id: str | None = None) -> int:
    if alert_id:
        with connect() as conn:
            cur = conn.execute("UPDATE alerts SET read_at = ? WHERE id = ? AND read_at IS NULL", (now_iso(), alert_id))
            conn.commit()
            return cur.rowcount
    with connect() as conn:
        cur = conn.execute("UPDATE alerts SET read_at = ? WHERE read_at IS NULL", (now_iso(),))
        conn.commit()
        return cur.rowcount


def log_run(status: str, checked: int, alerts: int, log: str = "") -> int:
    return execute(
        "INSERT INTO runs(started_at, finished_at, status, checked, alerts, log) VALUES(?,?,?,?,?,?)",
        (now_iso(), now_iso(), status, checked, alerts, log),
    )


def recent_runs(limit: int = 8) -> list[dict]:
    return query("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))


def prune_runs(keep: int = 40) -> None:
    with connect() as conn:
        conn.execute(
            "DELETE FROM runs WHERE id NOT IN (SELECT id FROM runs ORDER BY id DESC LIMIT ?)",
            (keep,),
        )
        conn.commit()


# --------------------------------------------------------------------------- #
# Seed / reset
# --------------------------------------------------------------------------- #

def _date(offset_days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=offset_days)).date().isoformat()


def seed(force: bool = False) -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES(?,?)", (key, value))
        conn.commit()
    seed_repos()
    if force:
        with connect() as conn:
            conn.executescript("DELETE FROM alerts; DELETE FROM snapshots; DELETE FROM watches; DELETE FROM runs;")
            conn.commit()
    if query_one("SELECT COUNT(*) AS c FROM watches")["c"] > 0:
        return

    seeds = [
        {
            "kind": "flight", "title": "Teresina → Lisboa", "origin": "THE", "destination": "LIS",
            "depart_date": _date(34), "return_date": _date(45), "cabin": "economy",
            "target_price": 4300, "base_price": 4890, "interval_minutes": 180,
        },
        {
            "kind": "flight", "title": "Teresina → Miami", "origin": "THE", "destination": "MIA",
            "depart_date": _date(61), "return_date": _date(70), "cabin": "economy",
            "target_price": 3600, "base_price": 4120, "interval_minutes": 240,
        },
        {
            "kind": "flight", "title": "Brasília → Paris", "origin": "BSB", "destination": "CDG",
            "depart_date": _date(88), "return_date": _date(99), "cabin": "premium_economy",
            "target_price": 6200, "base_price": 7350, "interval_minutes": 360,
        },
        {
            "kind": "hotel", "title": "Hotel em Lisboa", "hotel_name": "Memmo Alfama",
            "city": "Lisboa", "checkin": _date(34), "checkout": _date(39), "guests": 2, "rooms": 1,
            "target_price": 720, "base_price": 815, "interval_minutes": 180,
        },
        {
            "kind": "hotel", "title": "Hotel no Rio de Janeiro", "hotel_name": "Santa Clara",
            "city": "Rio de Janeiro", "checkin": _date(20), "checkout": _date(24), "guests": 2, "rooms": 1,
            "target_price": 580, "base_price": 690, "interval_minutes": 240,
        },
        # Pesquisa THE → POA (29/01/2027 a 01/02/2027) — referências de mercado
        {
            "kind": "flight", "title": "Teresina → Porto Alegre (29/01–01/02)",
            "origin": "THE", "destination": "POA",
            "depart_date": "2027-01-29", "return_date": "2027-02-01", "cabin": "economy",
            "target_price": 900, "base_price": 1050, "interval_minutes": 180,
        },
        {
            "kind": "hotel", "title": "Eko Residence Hotel", "hotel_name": "Eko Residence Hotel",
            "city": "Porto Alegre", "checkin": "2027-01-29", "checkout": "2027-02-01",
            "guests": 2, "rooms": 1, "target_price": 300, "base_price": 151, "interval_minutes": 180,
        },
        {
            "kind": "hotel", "title": "Intercity Porto Alegre Aeroporto", "hotel_name": "Intercity Porto Alegre Aeroporto",
            "city": "Porto Alegre", "checkin": "2027-01-29", "checkout": "2027-02-01",
            "guests": 2, "rooms": 1, "target_price": 300, "base_price": 194, "interval_minutes": 180,
        },
        {
            "kind": "hotel", "title": "Hotel Praça da Matriz", "hotel_name": "Hotel Praça da Matriz",
            "city": "Porto Alegre", "checkin": "2027-01-29", "checkout": "2027-02-01",
            "guests": 2, "rooms": 1, "target_price": 300, "base_price": 220, "interval_minutes": 180,
        },
        {
            "kind": "hotel", "title": "Novotel Porto Alegre Três Figueiras", "hotel_name": "Novotel Porto Alegre Três Figueiras",
            "city": "Porto Alegre", "checkin": "2027-01-29", "checkout": "2027-02-01",
            "guests": 2, "rooms": 1, "target_price": 300, "base_price": 220, "interval_minutes": 180,
        },
        {
            "kind": "hotel", "title": "Hotel Laghetto Viverone Moinhos", "hotel_name": "Hotel Laghetto Viverone Moinhos",
            "city": "Porto Alegre", "checkin": "2027-01-29", "checkout": "2027-02-01",
            "guests": 2, "rooms": 1, "target_price": 300, "base_price": 272, "interval_minutes": 180,
        },
    ]

    for data in seeds:
        watch = create_watch(data)
        _seed_history(watch)
        # marca a última checagem como agora
        execute("UPDATE watches SET last_checked_at = ? WHERE id = ?", (now_iso(), watch["id"]))

    # alertas de exemplo
    w = query_one("SELECT * FROM watches WHERE kind = 'hotel' ORDER BY created_at LIMIT 1")
    if w:
        add_alert(w["id"], "target", "Memmo Alfama atingiu a faixa de preço alvo em Lisboa.", 705.0)
    w2 = query_one("SELECT * FROM watches WHERE kind = 'flight' ORDER BY created_at LIMIT 1")
    if w2:
        add_alert(w2["id"], "drop", "Queda de 7,4% em Teresina → Lisboa nas últimas 24h.", 4520.0)
    log_run("seed", len(seeds), 2, "Dados de demonstração criados.")


def _seed_history(watch: dict) -> None:
    """Histórico determinístico de 30 dias (a cada 12h) terminando no preço atual."""
    points = 61
    base = float(watch["base_price"])
    rng = random.Random(int(hashlib.sha256(watch["id"].encode()).hexdigest()[:10], 16))
    prices: list[float] = []
    current = base
    for _ in range(points):
        current = current * (1 + rng.uniform(-0.018, 0.018))
        prices.append(round(current, 2))
    # normaliza para o preço final ficar próximo da base
    scale = base / prices[-1]
    prices = [round(p * scale, 2) for p in prices]
    start = datetime.now(timezone.utc) - timedelta(hours=12 * (points - 1))
    with connect() as conn:
        for i, price in enumerate(prices):
            found = start + timedelta(hours=12 * i)
            conn.execute(
                "INSERT INTO snapshots(watch_id, price, currency, provider, found_at, meta) VALUES(?,?,?,?,?,?)",
                (
                    watch["id"], price, watch["currency"], "demo",
                    found.replace(microsecond=0).isoformat(),
                    json.dumps({"mode": "demo", "seed": True}),
                ),
            )
        conn.commit()


def init() -> None:
    seed(force=False)


# --------------------------------------------------------------------------- #
# Catálogo de repositórios
# --------------------------------------------------------------------------- #

def list_repos() -> list[dict]:
    return query("SELECT * FROM repos ORDER BY stars DESC, name ASC")


def get_repo(repo_id: str) -> dict | None:
    return query_one("SELECT * FROM repos WHERE id = ?", (repo_id,))


def add_repo(data: dict) -> dict:
    name = str(data.get("name") or "").strip()
    url = str(data.get("url") or "").strip()
    if not name or not url:
        raise ValueError("Informe name e url.")
    if not url.startswith(("http://", "https://")):
        raise ValueError("A url deve começar com http:// ou https://.")
    repo = {
        "id": str(data.get("id") or new_id("repo")),
        "name": name,
        "url": url,
        "description": data.get("description") or "",
        "category": data.get("category") or "outros",
        "language": data.get("language") or "",
        "license": data.get("license") or "",
        "stars": int(data.get("stars") or 0),
        "mcp_url": data.get("mcp_url") or "",
        "install_cmd": data.get("install_cmd") or "",
        "best_for": data.get("best_for") or "",
        "added_at": now_iso(),
    }
    with connect() as conn:
        conn.execute(
            """INSERT INTO repos(id, name, url, description, category, language, license,
                                  stars, mcp_url, install_cmd, best_for, added_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(url) DO UPDATE SET
                 name = excluded.name,
                 description = excluded.description,
                 category = excluded.category,
                 language = excluded.language,
                 license = excluded.license,
                 stars = excluded.stars,
                 mcp_url = excluded.mcp_url,
                 install_cmd = excluded.install_cmd,
                 best_for = excluded.best_for""",
            tuple(repo.values()),
        )
        conn.commit()
    return query_one("SELECT * FROM repos WHERE url = ?", (url,))


def seed_repos() -> None:
    for repo in REPOS:
        with connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO repos(id, name, url, description, category, language,
                                              license, stars, mcp_url, install_cmd, best_for, added_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    repo["id"], repo["name"], repo["url"], repo.get("description", ""),
                    repo.get("category", ""), repo.get("language", ""), repo.get("license", ""),
                    repo.get("stars", 0), repo.get("mcp_url", ""), repo.get("install_cmd", ""),
                    repo.get("best_for", ""), now_iso(),
                ),
            )
            conn.commit()
