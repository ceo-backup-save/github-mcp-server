"""TripWatch AI — servidor HTTP, agendador e MCP server (stdlib, sem dependências).

Rodar:
    python3 app.py
    PORT=8787 python3 app.py

Endpoints principais:
    GET  /                 → painel web
    GET  /api/state        → watchlists + histórico + alertas + status
    POST /api/watches      → cria watchlist
    POST /api/watches/:id/check
    POST /api/check-all
    POST /api/agent/chat   → agente com ferramentas
    GET  /api/briefing     → briefing (local)
    POST /api/briefing     → briefing enriquecido por LLM (opcional)
    POST /mcp              → MCP JSON-RPC (tools/list, tools/call)
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent


def load_env_file() -> None:
    """Lê o .env local usando apenas a stdlib, sem sobrescrever o ambiente."""
    env_path = BASE_DIR / ".env"
    if not env_path.is_file():
        return
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()

import agent  # noqa: E402
import db  # noqa: E402
import engine  # noqa: E402
from providers import get_provider, provider_status  # noqa: E402

STATIC_DIR = BASE_DIR / "static"
HOST = os.environ.get("TRIPWATCH_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", os.environ.get("TRIPWATCH_PORT", "8787")))
STOP_EVENT = threading.Event()
SCHEDULER_THREAD: threading.Thread | None = None

MCP_TOOLS = [
    {
        "name": "search_flights",
        "description": "Busca preços de voos (Google Flights via SerpAPI quando configurado; simulador caso contrário).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Código IATA de origem, ex.: THE"},
                "destination": {"type": "string", "description": "Código IATA de destino, ex.: LIS"},
                "depart_date": {"type": "string", "description": "YYYY-MM-DD"},
                "return_date": {"type": "string", "description": "YYYY-MM-DD (opcional)"},
                "cabin": {"type": "string", "enum": ["economy", "premium_economy", "business", "first"]},
            },
            "required": ["origin", "destination", "depart_date"],
        },
    },
    {
        "name": "search_hotels",
        "description": "Busca preços de hotéis por cidade ou nome do hotel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Cidade ou nome do hotel"},
                "checkin": {"type": "string", "description": "YYYY-MM-DD"},
                "checkout": {"type": "string", "description": "YYYY-MM-DD"},
                "guests": {"type": "integer", "minimum": 1},
                "rooms": {"type": "integer", "minimum": 1},
            },
            "required": ["city", "checkin", "checkout"],
        },
    },
    {
        "name": "track_flight",
        "description": "Cria um monitoramento de voo com checagem agendada e alerta de preço-alvo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "depart_date": {"type": "string"},
                "return_date": {"type": "string"},
                "target_price": {"type": "number"},
                "cabin": {"type": "string"},
                "interval_minutes": {"type": "integer", "minimum": 15},
            },
            "required": ["origin", "destination", "depart_date", "target_price"],
        },
    },
    {
        "name": "track_hotel",
        "description": "Cria um monitoramento de hotel com checagem agendada e alerta de preço-alvo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "hotel_name": {"type": "string"},
                "checkin": {"type": "string"},
                "checkout": {"type": "string"},
                "target_price": {"type": "number"},
                "guests": {"type": "integer", "minimum": 1},
                "rooms": {"type": "integer", "minimum": 1},
                "interval_minutes": {"type": "integer", "minimum": 15},
            },
            "required": ["city", "checkin", "checkout", "target_price"],
        },
    },
    {
        "name": "list_watchlist",
        "description": "Lista os itens monitorados com preço atual, alvo e recomendação do agente.",
        "inputSchema": {"type": "object", "properties": {"kind": {"type": "string", "enum": ["flight", "hotel"]}}},
    },
    {
        "name": "get_price_history",
        "description": "Retorna o histórico de preços de um watchlist.",
        "inputSchema": {
            "type": "object",
            "properties": {"watch_id": {"type": "string"}},
            "required": ["watch_id"],
        },
    },
    {
        "name": "run_check",
        "description": "Executa uma checagem imediatamente (todos os itens se watch_id for omitido).",
        "inputSchema": {"type": "object", "properties": {"watch_id": {"type": "string"}}},
    },
    {
        "name": "travel_briefing",
        "description": "Briefing do agente com oportunidades, economia potencial e próximos passos.",
        "inputSchema": {"type": "object", "properties": {"use_llm": {"type": "boolean"}}},
    },
    {
        "name": "list_alerts",
        "description": "Lista os alertas de preço mais recentes.",
        "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}}},
    },
    {
        "name": "update_target",
        "description": "Atualiza o preço-alvo de um watchlist.",
        "inputSchema": {
            "type": "object",
            "properties": {"watch_id": {"type": "string"}, "target_price": {"type": "number"}},
            "required": ["watch_id", "target_price"],
        },
    },
    {
        "name": "delete_watch",
        "description": "Remove um item do monitoramento.",
        "inputSchema": {"type": "object", "properties": {"watch_id": {"type": "string"}}, "required": ["watch_id"]},
    },
    {
        "name": "agent_chat",
        "description": "Conversa com o agente em linguagem natural (cria watchlists, consulta preços, roda checagens).",
        "inputSchema": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
    },
]


# --------------------------------------------------------------------------- #
# Helpers de domínio
# --------------------------------------------------------------------------- #

def estimate_base(kind: str, key: str) -> float:
    return agent._estimate_base(kind, key)


def state_payload() -> dict:
    watches = db.list_watches()
    enriched = []
    for watch in watches:
        item = dict(watch)
        item["analysis"] = agent.analyze(watch)
        enriched.append(item)
    alerts = db.list_alerts(limit=40)
    unread = db.query_one("SELECT COUNT(*) AS c FROM alerts WHERE read_at IS NULL")["c"]
    with_data = [w for w in enriched if w["analysis"].get("current") is not None]
    below_target = [
        w for w in with_data
        if w.get("target_price") and w["analysis"]["current"] <= float(w["target_price"]) * 1.01
    ]
    potential = sum(w["analysis"].get("savings_vs_target") or 0 for w in with_data)
    return {
        "watches": enriched,
        "alerts": alerts,
        "settings": db.all_settings(),
        "provider": provider_status(),
        "scheduler": {
            "running": bool(SCHEDULER_THREAD and SCHEDULER_THREAD.is_alive()),
            "tick_seconds": 20,
            "next_check": engine.next_check(),
        },
        "runs": db.recent_runs(6),
        "briefing": agent.build_briefing(),
        "stats": {
            "watches": len(watches),
            "active": sum(1 for w in watches if w["active"]),
            "flights": sum(1 for w in watches if w["kind"] == "flight"),
            "hotels": sum(1 for w in watches if w["kind"] == "hotel"),
            "unread_alerts": unread,
            "below_target": len(below_target),
            "potential_savings": round(potential, 2),
            "snapshots": db.query_one("SELECT COUNT(*) AS c FROM snapshots")["c"],
            "currency": db.get_setting("currency", "BRL"),
        },
        "server_time": db.now_iso(),
    }


def create_watch_from_payload(payload: dict) -> dict:
    kind = payload.get("kind", "flight")
    if kind not in ("flight", "hotel"):
        raise ValueError("kind deve ser 'flight' ou 'hotel'")
    data = dict(payload)
    data["kind"] = kind
    if kind == "flight":
        if not data.get("origin") or not data.get("destination") or not data.get("depart_date"):
            raise ValueError("Informe origin, destination e depart_date.")
        data["origin"] = str(data["origin"]).upper()
        data["destination"] = str(data["destination"]).upper()
        data.setdefault("title", f"{data['origin']} → {data['destination']}")
    else:
        if not data.get("city") and not data.get("hotel_name"):
            raise ValueError("Informe city ou hotel_name.")
        if not data.get("checkin") or not data.get("checkout"):
            raise ValueError("Informe checkin e checkout.")
        data.setdefault("title", f"Hotel em {data.get('city') or data.get('hotel_name')}")
    if not data.get("base_price"):
        key = f"{kind}:{data.get('origin')}{data.get('destination')}{data.get('city')}{data.get('hotel_name')}"
        data["base_price"] = estimate_base(kind, key)
    if not data.get("target_price"):
        data["target_price"] = round(float(data["base_price"]) * 0.9, 2)
    data["currency"] = data.get("currency") or db.get_setting("currency", "BRL")
    return db.create_watch(data)


def run_check_and_brief(watch_id: str) -> dict:
    result = engine.run_check(watch_id, force=True)
    watch = db.get_watch(watch_id)
    if watch:
        result["analysis"] = agent.analyze(watch)
    return result


# --------------------------------------------------------------------------- #
# MCP
# --------------------------------------------------------------------------- #

def mcp_tool_result(payload: dict) -> dict:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
        "isError": False,
    }


def mcp_call_tool(name: str, arguments: dict) -> dict:
    args = arguments or {}
    if name == "search_flights":
        provider = get_provider()
        ephemeral = {
            "id": "ephemeral", "kind": "flight", "currency": db.get_setting("currency", "BRL"),
            "origin": args.get("origin", "").upper(), "destination": args.get("destination", "").upper(),
            "depart_date": args.get("depart_date"), "return_date": args.get("return_date"),
            "cabin": args.get("cabin", "economy"), "base_price": 4000,
        }
        result = provider.search(ephemeral)
        return {"origin": ephemeral["origin"], "destination": ephemeral["destination"], **result.__dict__}
    if name == "search_hotels":
        provider = get_provider()
        ephemeral = {
            "id": "ephemeral", "kind": "hotel", "currency": db.get_setting("currency", "BRL"),
            "city": args.get("city"), "hotel_name": args.get("hotel_name") or args.get("city"),
            "checkin": args.get("checkin"), "checkout": args.get("checkout"),
            "guests": args.get("guests", 1), "rooms": args.get("rooms", 1), "base_price": 700,
        }
        result = provider.search(ephemeral)
        return {"city": args.get("city"), **result.__dict__}
    if name == "track_flight":
        watch = create_watch_from_payload({
            "kind": "flight", "origin": args.get("origin"), "destination": args.get("destination"),
            "depart_date": args.get("depart_date"), "return_date": args.get("return_date"),
            "cabin": args.get("cabin", "economy"), "target_price": args.get("target_price"),
            "interval_minutes": args.get("interval_minutes", 180),
        })
        return {"watch": watch, "check": run_check_and_brief(watch["id"])}
    if name == "track_hotel":
        watch = create_watch_from_payload({
            "kind": "hotel", "city": args.get("city"), "hotel_name": args.get("hotel_name"),
            "checkin": args.get("checkin"), "checkout": args.get("checkout"),
            "guests": args.get("guests", 2), "rooms": args.get("rooms", 1),
            "target_price": args.get("target_price"),
            "interval_minutes": args.get("interval_minutes", 180),
        })
        return {"watch": watch, "check": run_check_and_brief(watch["id"])}
    if name == "list_watchlist":
        watches = db.list_watches(args.get("kind"))
        return {
            "watches": [
                {**w, "snapshots": len(w["snapshots"]), "analysis": agent.analyze(w)}
                for w in watches
            ]
        }
    if name == "get_price_history":
        watch = db.get_watch(args.get("watch_id", ""))
        if not watch:
            raise ValueError("watch_id não encontrado")
        return {"watch": watch, "history": db.query(
            "SELECT price, currency, provider, found_at FROM snapshots WHERE watch_id = ? ORDER BY found_at ASC",
            (watch["id"],),
        )}
    if name == "run_check":
        watch_id = args.get("watch_id")
        if watch_id:
            return run_check_and_brief(watch_id)
        return engine.run_check_all(force=True)
    if name == "travel_briefing":
        briefing = agent.build_briefing()
        if args.get("use_llm"):
            briefing = agent.briefing_with_llm(briefing)
        return briefing
    if name == "list_alerts":
        return {"alerts": db.list_alerts(limit=int(args.get("limit", 20)))}
    if name == "update_target":
        watch = db.update_watch(args.get("watch_id", ""), {"target_price": args.get("target_price")})
        if not watch:
            raise ValueError("watch_id não encontrado")
        return {"watch": watch, "analysis": agent.analyze(watch)}
    if name == "delete_watch":
        db.delete_watch(args.get("watch_id", ""))
        return {"ok": True, "deleted": args.get("watch_id")}
    if name == "agent_chat":
        return agent.chat(args.get("message", ""))
    raise ValueError(f"Ferramenta desconhecida: {name}")


def handle_mcp(payload: dict) -> dict | None:
    method = payload.get("method")
    request_id = payload.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "tripwatch-ai", "version": "1.0.0"},
            },
        }
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": MCP_TOOLS}}
    if method == "tools/call":
        params = payload.get("params") or {}
        try:
            result = mcp_call_tool(params.get("name", ""), params.get("arguments") or {})
            return {"jsonrpc": "2.0", "id": request_id, "result": mcp_tool_result(result)}
        except Exception as exc:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "result": {"content": [{"type": "text", "text": f"Erro: {exc}"}], "isError": True},
            }
    if request_id is None:
        return None
    return {
        "jsonrpc": "2.0", "id": request_id,
        "error": {"code": -32601, "message": f"Método não suportado: {method}"},
    }


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

class Handler(BaseHTTPRequestHandler):
    server_version = "TripWatchAI/1.0"
    protocol_version = "HTTP/1.1"

    # -- infra ------------------------------------------------------------- #
    def log_message(self, fmt: str, *args) -> None:  # silêncio no preview
        pass

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Mcp-Session-Id, Last-Event-ID")
        self.send_header("Access-Control-Expose-Headers", "Mcp-Session-Id")

    def _send(self, status: int, body: bytes, content_type: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        if length > 2_000_000:
            raise ValueError("payload muito grande")
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as exc:
            raise ValueError("JSON inválido") from exc

    def _serve_static(self, path: str) -> None:
        relative = path.lstrip("/")
        if relative in ("", "index.html"):
            relative = "index.html"
        target = (STATIC_DIR / relative).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.is_file():
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in ("application/javascript", "application/json"):
            content_type += "; charset=utf-8"
        self._send(200, target.read_bytes(), content_type)

    # -- verbos ------------------------------------------------------------ #
    def do_OPTIONS(self) -> None:
        self._send(204, b"", "text/plain")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            self._serve_static("index.html")
            return
        if path.startswith("/static/"):
            self._serve_static(path[len("/static/"):])
            return
        if path == "/api/health":
            self._json(200, {"ok": True, "service": "tripwatch-ai", "time": db.now_iso()})
            return
        if path == "/api/state":
            self._json(200, state_payload())
            return
        if path == "/api/briefing":
            briefing = agent.build_briefing()
            query = parse_qs(parsed.query)
            if query.get("llm", ["0"])[0] in ("1", "true"):
                briefing = agent.briefing_with_llm(briefing)
            self._json(200, briefing)
            return
        if path == "/api/agent/context":
            self._json(200, agent.agent_context())
            return
        if path == "/api/runs":
            self._json(200, {"runs": db.recent_runs(20)})
            return
        if path == "/mcp":
            self._json(200, {
                "name": "tripwatch-ai",
                "version": "1.0.0",
                "transport": "Streamable HTTP (JSON-RPC 2.0)",
                "endpoint": "/mcp",
                "tools": [t["name"] for t in MCP_TOOLS],
                "initialize": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}},
            })
            return
        self._send(404, b'{"error":"not found"}', "application/json")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            payload = self._body()
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
            return

        if path == "/mcp":
            response = handle_mcp(payload)
            if response is None:
                self._send(202, b"", "text/plain")
            else:
                self._json(200, response)
            return

        if path == "/api/watches":
            try:
                watch = create_watch_from_payload(payload)
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
                return
            result = run_check_and_brief(watch["id"])
            self._json(201, {"watch": watch, "check": result})
            return

        if path == "/api/check-all":
            self._json(200, engine.run_check_all(force=True))
            return

        if path == "/api/alerts/read":
            count = db.mark_alerts_read(payload.get("id"))
            self._json(200, {"ok": True, "updated": count})
            return

        if path == "/api/agent/chat":
            self._json(200, agent.chat(payload.get("message", "")))
            return

        if path == "/api/briefing":
            briefing = agent.build_briefing()
            if payload.get("use_llm", True):
                briefing = agent.briefing_with_llm(briefing)
            self._json(200, briefing)
            return

        if path == "/api/settings":
            for key, value in (payload.get("settings") or payload).items():
                if key in db.DEFAULT_SETTINGS:
                    db.set_setting(key, value)
            self._json(200, {"ok": True, "settings": db.all_settings()})
            return

        if path == "/api/reset-demo":
            db.seed(force=True)
            self._json(200, {"ok": True})
            return

        match = re.match(r"^/api/watches/([A-Za-z0-9_]+)/check$", path)
        if match:
            self._json(200, run_check_and_brief(match.group(1)))
            return

        match = re.match(r"^/api/watches/([A-Za-z0-9_]+)$", path)
        if match:
            watch = db.update_watch(match.group(1), payload)
            if not watch:
                self._json(404, {"error": "watch não encontrado"})
                return
            self._json(200, {"watch": watch, "analysis": agent.analyze(watch)})
            return

        self._send(404, b'{"error":"not found"}', "application/json")

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        match = re.match(r"^/api/watches/([A-Za-z0-9_]+)$", parsed.path)
        if not match:
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        try:
            payload = self._body()
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
            return
        watch = db.update_watch(match.group(1), payload)
        if not watch:
            self._json(404, {"error": "watch não encontrado"})
            return
        self._json(200, {"watch": watch, "analysis": agent.analyze(watch)})

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        match = re.match(r"^/api/watches/([A-Za-z0-9_]+)$", parsed.path)
        if not match:
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        db.delete_watch(match.group(1))
        self._json(200, {"ok": True})


def main() -> None:
    db.init()
    global SCHEDULER_THREAD
    if not os.environ.get("TRIPWATCH_DISABLE_SCHEDULER"):
        SCHEDULER_THREAD = threading.Thread(
            target=engine.scheduler_loop, args=(STOP_EVENT,), name="tripwatch-scheduler", daemon=True
        )
        SCHEDULER_THREAD.start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"TripWatch AI em http://{HOST}:{PORT}  (MCP: /mcp)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        STOP_EVENT.set()
        server.server_close()


if __name__ == "__main__":
    main()
