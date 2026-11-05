"""Motor de checagem: executa o provedor, grava histórico e gera alertas."""
from __future__ import annotations

import threading
from datetime import datetime, timezone

import db
from providers import ProviderError, demo_price, get_provider

_lock = threading.Lock()


def _hours_ago(hours: int) -> str:
    from datetime import timedelta

    return (datetime.now(timezone.utc) - timedelta(hours=hours)).replace(microsecond=0).isoformat()


def _has_recent_alert(watch_id: str, kind: str, hours: int = 8) -> bool:
    row = db.query_one(
        "SELECT id FROM alerts WHERE watch_id = ? AND kind = ? AND created_at >= ? LIMIT 1",
        (watch_id, kind, _hours_ago(hours)),
    )
    return row is not None


def run_check(watch_id: str, force: bool = False) -> dict:
    """Executa uma busca para o watchlist e persiste o resultado."""
    with _lock:
        watch = db.get_watch(watch_id)
        if not watch:
            return {"ok": False, "error": "Watch não encontrado."}
        if not watch["active"] and not force:
            return {"ok": False, "error": "Watch pausado."}

        provider = get_provider()
        try:
            result = provider.search(watch)
            price, provider_used, meta = result.price, result.provider, result.meta
        except ProviderError as exc:
            price, meta = demo_price(watch)
            provider_used = "demo"
            meta = {"mode": "fallback", "error": str(exc), "note": "Provedor real falhou; usando simulador."}

        previous = db.query_one(
            "SELECT price FROM snapshots WHERE watch_id = ? ORDER BY found_at DESC LIMIT 1",
            (watch_id,),
        )
        prev_price = previous["price"] if previous else None
        db.add_snapshot(watch_id, price, provider_used, meta)
        db.execute("UPDATE watches SET last_checked_at = ? WHERE id = ?", (db.now_iso(), watch_id))

        alerts: list[dict] = []
        target = watch["target_price"]
        if target and price <= float(target):
            if not _has_recent_alert(watch_id, "target"):
                alerts.append(
                    db.add_alert(
                        watch_id,
                        "target",
                        f"{watch['title']}: preço em R$ {price:,.2f} atingiu o alvo de R$ {float(target):,.2f}.",
                        price,
                    )
                )

        if prev_price:
            change = (price - prev_price) / prev_price * 100
            threshold = float(db.get_setting("alert_drop_pct", "5"))
            if change <= -threshold and not _has_recent_alert(watch_id, "drop"):
                alerts.append(
                    db.add_alert(
                        watch_id,
                        "drop",
                        f"{watch['title']}: queda de {abs(change):.1f}% (R$ {prev_price:,.2f} → R$ {price:,.2f}).",
                        price,
                    )
                )
            elif change >= 8 and not _has_recent_alert(watch_id, "rise"):
                alerts.append(
                    db.add_alert(
                        watch_id,
                        "rise",
                        f"{watch['title']}: alta de {change:.1f}% (R$ {prev_price:,.2f} → R$ {price:,.2f}).",
                        price,
                    )
                )

        return {
            "ok": True,
            "watch_id": watch_id,
            "price": price,
            "previous": prev_price,
            "currency": watch["currency"],
            "provider": provider_used,
            "alerts": len(alerts),
            "meta": meta,
        }


def run_check_all(force: bool = False, only_id: str | None = None) -> dict:
    watches = db.list_watches()
    if only_id:
        watches = [w for w in watches if w["id"] == only_id]
    checked = 0
    alerts = 0
    errors = 0
    log: list[str] = []
    for watch in watches:
        if not watch["active"] and not force:
            continue
        if not force and watch["last_checked_at"]:
            last = datetime.fromisoformat(watch["last_checked_at"])
            due = last.timestamp() + watch["interval_minutes"] * 60
            if datetime.now(timezone.utc).timestamp() < due:
                continue
        result = run_check(watch["id"], force=force)
        if result.get("ok"):
            checked += 1
            alerts += result.get("alerts", 0)
            log.append(f"{watch['title']}: R$ {result['price']:,.2f} ({result['provider']})")
        else:
            errors += 1
            log.append(f"{watch['title']}: {result.get('error')}")
    db.log_run("ok" if errors == 0 else "partial", checked, alerts, " | ".join(log)[:4000])
    db.prune_runs()
    return {"ok": True, "checked": checked, "alerts": alerts, "errors": errors, "log": log}


def due_watches() -> list[dict]:
    now = datetime.now(timezone.utc).timestamp()
    due = []
    for watch in db.list_watches():
        if not watch["active"]:
            continue
        if not watch["last_checked_at"]:
            due.append(watch)
            continue
        last = datetime.fromisoformat(watch["last_checked_at"]).timestamp()
        if now >= last + watch["interval_minutes"] * 60:
            due.append(watch)
    return due


def next_check() -> dict | None:
    now = datetime.now(timezone.utc).timestamp()
    best: tuple[float, dict] | None = None
    for watch in db.list_watches():
        if not watch["active"]:
            continue
        if not watch["last_checked_at"]:
            ts = now
        else:
            ts = datetime.fromisoformat(watch["last_checked_at"]).timestamp() + watch["interval_minutes"] * 60
        if best is None or ts < best[0]:
            best = (ts, watch)
    if not best:
        return None
    return {"at": datetime.fromtimestamp(best[0], tz=timezone.utc).isoformat(), "watch": best[1]["title"]}


def scheduler_loop(stop_event: threading.Event, interval_seconds: int = 20) -> None:
    """Loop do agendador: roda checks vencidos e mantém o histórico vivo."""
    while not stop_event.is_set():
        try:
            due = due_watches()
            if due:
                run_check_all(force=False)
        except Exception as exc:  # o agendador nunca deve derrubar o processo
            print(f"[scheduler] erro: {exc}", flush=True)
        stop_event.wait(interval_seconds)
