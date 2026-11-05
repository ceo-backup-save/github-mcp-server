"""Agente do TripWatch: análise de tendência, briefing e chat com ferramentas."""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

import db

UNIT = {"flight": "pessoa", "hotel": "diária"}
CURRENCY_SYMBOL = {"BRL": "R$", "USD": "US$", "EUR": "€"}


def _money(value: float | None, currency: str = "BRL") -> str:
    if value is None:
        return "—"
    symbol = CURRENCY_SYMBOL.get(currency, "")
    return f"{symbol} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value).strftime("%d/%m")
    except ValueError:
        return value


def _stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5


def _slope_pct(prices: list[float]) -> float:
    """Variação percentual média por ponto (regressão linear simples)."""
    n = len(prices)
    if n < 3:
        return 0.0
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(prices) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, prices))
    den = sum((x - mean_x) ** 2 for x in xs)
    if den == 0 or mean_y == 0:
        return 0.0
    return (num / den) / mean_y * 100


def analyze(watch: dict) -> dict:
    snaps = watch.get("snapshots") or []
    prices = [float(s["price"]) for s in snaps]
    currency = watch.get("currency", "BRL")
    unit = UNIT.get(watch["kind"], "unidade")
    target = watch.get("target_price")
    target = float(target) if target else None

    if not prices:
        return {
            "watch_id": watch["id"], "title": watch["title"], "kind": watch["kind"],
            "recommendation": "watch", "label": "Sem dados", "confidence": 0,
            "reasons": ["Ainda não há preço coletado para este item."],
            "current": None, "unit": unit, "currency": currency,
        }

    current = prices[-1]
    average = sum(prices) / len(prices)
    low = min(prices)
    high = max(prices)
    low_idx = prices.index(low)
    low_at = snaps[low_idx]["found_at"] if low_idx < len(snaps) else None
    previous = prices[-2] if len(prices) > 1 else current
    change_pct = ((current - previous) / previous * 100) if previous else 0.0

    week_ago = None
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    for snap in snaps:
        try:
            if datetime.fromisoformat(snap["found_at"]) <= cutoff:
                week_ago = float(snap["price"])
        except ValueError:
            continue
    change_week = ((current - week_ago) / week_ago * 100) if week_ago else 0.0
    slope = _slope_pct(prices[-30:])
    volatility = _stdev(prices[-30:]) / average if average else 0

    reasons: list[str] = []
    reasons.append(
        f"Preço atual de {_money(current, currency)}/{unit} está "
        f"{abs((current - average) / average * 100):.1f}% "
        f"{'abaixo' if current <= average else 'acima'} da média histórica ({_money(average, currency)})."
    )
    reasons.append(f"Mínimo registrado: {_money(low, currency)} em {_date(low_at)} · máximo: {_money(high, currency)}.")
    if week_ago:
        reasons.append(f"Últimos 7 dias: {'queda' if change_week <= 0 else 'alta'} de {abs(change_week):.1f}%.")
    if target:
        gap = current - target
        if gap <= 0:
            reasons.append(f"Está {_money(abs(gap), currency)} abaixo do seu alvo de {_money(target, currency)}.")
        else:
            reasons.append(f"Faltam {_money(gap, currency)} para o alvo de {_money(target, currency)}.")
    if volatility > 0.06:
        reasons.append("Volatilidade alta: vale repetir a checagem antes de comprar.")

    recommendation = "watch"
    label = "Observar"
    if target and current <= target * 1.01:
        recommendation, label = "buy", "Comprar agora"
    elif current <= low * 1.025 and current <= average * 0.975:
        recommendation, label = "buy", "Comprar agora"
    elif change_week > 3.5 or (slope > 0.25 and current > average * 1.01):
        recommendation, label = "wait", "Aguardar"

    confidence = 45 + min(32, len(prices) * 0.8) + (8 if target else 0) - min(18, volatility * 120)
    confidence = int(max(38, min(96, confidence)))

    return {
        "watch_id": watch["id"],
        "title": watch["title"],
        "kind": watch["kind"],
        "recommendation": recommendation,
        "label": label,
        "confidence": confidence,
        "reasons": reasons,
        "current": round(current, 2),
        "average": round(average, 2),
        "low": round(low, 2),
        "high": round(high, 2),
        "change_pct": round(change_pct, 2),
        "change_week": round(change_week, 2),
        "target": target,
        "unit": unit,
        "currency": currency,
        "points": len(prices),
        "savings_vs_target": round(max(0.0, target - current), 2) if target else None,
        "gap_to_target": round(current - target, 2) if target else None,
    }


def build_briefing() -> dict:
    watches = db.list_watches()
    analyses = [analyze(w) for w in watches]
    with_data = [a for a in analyses if a.get("current") is not None]
    opportunities = sorted(
        with_data,
        key=lambda a: (
            0 if a["recommendation"] == "buy" else 1 if a["recommendation"] == "wait" else 2,
            a.get("gap_to_target") if a.get("gap_to_target") is not None else 1e9,
        ),
    )
    alerts = db.list_alerts(limit=8)
    unread = db.query_one("SELECT COUNT(*) AS c FROM alerts WHERE read_at IS NULL")["c"]
    potential = sum(a.get("savings_vs_target") or 0 for a in with_data)
    below_target = [a for a in with_data if a.get("target") and a["current"] <= a["target"] * 1.01]
    flights = [a for a in with_data if a["kind"] == "flight"]
    hotels = [a for a in with_data if a["kind"] == "hotel"]

    lines: list[str] = []
    lines.append(
        f"Analisei {len(watches)} watchlist(s) — {len(flights)} voo(s) e {len(hotels)} hotel(is) — "
        f"com {sum(a['points'] for a in with_data)} pontos de preço no histórico."
    )
    if below_target:
        names = ", ".join(a["title"] for a in below_target[:3])
        lines.append(f"{len(below_target)} item(ns) estão no preço-alvo: {names}. Este é o melhor momento para comprar.")
    if opportunities:
        top = opportunities[0]
        if top["recommendation"] == "buy":
            lines.append(f"Maior oportunidade: {top['title']} a {_money(top['current'], top['currency'])}/{top['unit']}.")
        elif top["recommendation"] == "wait":
            lines.append(f"Tendência de alta em {top['title']}; se puder esperar, acompanhe mais 24–48h.")
        else:
            lines.append(f"Sem sinal forte de compra. O melhor cenário monitorado é {top['title']}.")
    if potential > 0:
        lines.append(f"Economia potencial acumulada até os alvos definidos: {_money(potential)}.")
    if unread:
        lines.append(f"Você tem {unread} alerta(s) não lido(s).")
    lines.append("Recomendação operacional: mantenha as checagens agendadas e compre quando o preço cruzar o alvo com confiança acima de 70%.")

    return {
        "generated_at": db.now_iso(),
        "text": " ".join(lines),
        "stats": {
            "watches": len(watches),
            "flights": len(flights),
            "hotels": len(hotels),
            "with_data": len(with_data),
            "below_target": len(below_target),
            "unread_alerts": unread,
            "potential_savings": round(potential, 2),
            "currency": db.get_setting("currency", "BRL"),
        },
        "opportunities": [
            {
                "watch_id": a["watch_id"], "title": a["title"], "kind": a["kind"],
                "recommendation": a["recommendation"], "label": a["label"],
                "current": a["current"], "target": a.get("target"),
                "currency": a["currency"], "unit": a["unit"], "confidence": a["confidence"],
            }
            for a in opportunities[:5]
        ],
        "alerts": alerts,
        "llm": False,
    }


# --------------------------------------------------------------------------- #
# LLM opcional (OpenAI, Anthropic ou endpoint compatível)
# --------------------------------------------------------------------------- #

def llm_configured() -> bool:
    return bool(
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or (os.environ.get("LLM_API_KEY") and os.environ.get("LLM_BASE_URL"))
    )


def llm_complete(system: str, user: str, max_tokens: int = 700) -> str | None:
    try:
        if os.environ.get("ANTHROPIC_API_KEY"):
            body = json.dumps({
                "model": os.environ.get("LLM_MODEL", "claude-3-5-sonnet-latest"),
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=body,
                headers={
                    "content-type": "application/json",
                    "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
            return "\n".join(parts).strip() or None

        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
        base = (os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        model = os.environ.get("LLM_MODEL") or ("gpt-4o-mini" if os.environ.get("OPENAI_API_KEY") else "llama3.1")
        body = json.dumps({
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }).encode()
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=body,
            headers={"content-type": "application/json", "authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return (data["choices"][0]["message"]["content"] or "").strip() or None
    except Exception as exc:
        print(f"[llm] falhou: {exc}", flush=True)
        return None


def briefing_with_llm(briefing: dict) -> dict:
    if not llm_configured():
        briefing["llm"] = False
        briefing["llm_note"] = "Nenhuma chave de LLM configurada (OPENAI_API_KEY / ANTHROPIC_API_KEY). Usando análise local."
        return briefing
    context = json.dumps(
        {
            "stats": briefing["stats"],
            "oportunidades": briefing["opportunities"],
            "alertas": [
                {"tipo": a["kind"], "mensagem": a["message"], "quando": a["created_at"]}
                for a in briefing["alerts"][:5]
            ],
        },
        ensure_ascii=False,
    )
    system = (
        "Você é o TripWatch Agent, um especialista em viagens que monitora preços de voos e hotéis. "
        "Responda em português do Brasil, em no máximo 150 palavras, com tom consultivo e direto. "
        "Use os dados fornecidos, destaque as melhores oportunidades e diga o que fazer agora. "
        "Não invente preços que não estejam no contexto."
    )
    user = f"Contexto do monitoramento em JSON:\n{context}\n\nGere o briefing do dia."
    text = llm_complete(system, user)
    if text:
        briefing["text"] = text
        briefing["llm"] = True
    else:
        briefing["llm"] = False
        briefing["llm_note"] = "Falha ao chamar o LLM; mantendo a análise local."
    return briefing


# --------------------------------------------------------------------------- #
# Chat / comandos
# --------------------------------------------------------------------------- #

def _norm(text: str) -> str:
    import unicodedata

    text = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


CITY_IATA = {
    "teresina": "THE", "lisboa": "LIS", "lisbon": "LIS", "miami": "MIA", "paris": "CDG",
    "brasilia": "BSB", "rio de janeiro": "RIO", "rio": "RIO", "galeao": "GIG",
    "sao paulo": "SAO", "guarulhos": "GRU", "london": "LON", "new york": "NYC",
    "tokyo": "TYO", "rome": "ROM", "floripa": "FLN", "porto": "OPO", "madrid": "MAD",
    "barcelona": "BCN", "buenos aires": "BUE", "santiago": "SCL", "lima": "LIM",
    "bogota": "BOG", "amsterdam": "AMS", "berlin": "BER", "frankfurt": "FRA",
    "zurich": "ZRH", "dubai": "DXB", "istanbul": "IST", "mexico city": "MEX",
    "cancun": "CUN", "orlando": "MCO", "new york city": "NYC", "los angeles": "LAX",
    "san francisco": "SFO", "chicago": "ORD", "boston": "BOS", "washington": "IAD",
    "recife": "REC", "fortaleza": "FOR", "salvador": "SSA", "belem": "BEL",
    "manaus": "MAO", "curitiba": "CWB", "porto alegre": "POA", "belo horizonte": "CNF",
}


def _extract_route(text: str) -> tuple[str, str] | None:
    codes = re.findall(r"\b([A-Z]{3})\b", text)
    if len(codes) >= 2:
        return codes[0], codes[1]
    match = re.search(r"\bde\s+([A-Za-z]{3})\s+para\s+([A-Za-z]{3})\b", text, re.IGNORECASE)
    if match:
        return match.group(1).upper(), match.group(2).upper()

    # rotas escritas por cidade: "Teresina → Lisboa", "de Miami para Paris"
    norm = _norm(text)
    found: list[tuple[int, str, str]] = []
    for city, code in CITY_IATA.items():
        index = norm.find(city)
        if index >= 0:
            found.append((index, city, code))
    found.sort()
    unique: list[tuple[int, str, str]] = []
    for item in found:
        if all(item[2] != other[2] for other in unique):
            unique.append(item)
    if len(unique) >= 2:
        return unique[0][2], unique[1][2]
    return None


def _extract_city(norm: str) -> str | None:
    match = re.search(r"(?:hotel|hospedagem|estadia|stay)\s+(?:em|no|na|para)\s+([a-z\s]+?)(?=\s+(?:de|para|em|com|abaixo|ate|target|no dia)\b|[,.]|$)", norm)
    if not match:
        return None
    city = match.group(1).strip()
    return city.title() if city else None


def _extract_dates(norm: str) -> list[datetime]:
    today = datetime.now(timezone.utc).date()
    found: list[datetime] = []
    for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})", norm):
        try:
            found.append(datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc))
        except ValueError:
            pass
    for m in re.finditer(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", norm):
        day, month = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        if year < 100:
            year += 2000
        try:
            found.append(datetime(year, month, day, tzinfo=timezone.utc))
        except ValueError:
            pass
    return found


def _parse_number(raw: str) -> float | None:
    """Aceita 4300, 4.300, 4,300.00, 4300.50."""
    raw = raw.strip()
    if not raw:
        return None
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    elif raw.count(".") == 1 and len(raw.split(".")[1]) == 3 and len(raw.split(".")[0]) <= 3:
        raw = raw.replace(".", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _extract_target(norm: str) -> float | None:
    patterns = [
        r"(?:abaixo de|ate|maximo|target|alvo)\s*(?:r\$|reais)?\s*([\d][\d.,]{2,9})",
        r"r\$\s*([\d][\d.,]{2,9})",
    ]
    for pattern in patterns:
        match = re.search(pattern, norm)
        if match:
            value = _parse_number(match.group(1))
            if value:
                return value
    return None


def _estimate_base(kind: str, key: str) -> float:
    rng = random.Random(int(hashlib.sha256(key.encode()).hexdigest()[:10], 16))
    if kind == "flight":
        return round(rng.uniform(2900, 7200), 2)
    return round(rng.uniform(420, 1150), 2)


def _parse_new_watch(message: str) -> dict | None:
    norm = _norm(message)
    route = _extract_route(message)
    city = _extract_city(norm)
    if not route and not city:
        return None
    dates = _extract_dates(norm)
    target = _extract_target(norm)
    kind = "flight" if route else "hotel"
    if kind == "flight":
        depart = dates[0] if dates else datetime.now(timezone.utc) + timedelta(days=30)
        ret = dates[1] if len(dates) > 1 else depart + timedelta(days=7)
        base = _estimate_base("flight", f"{route[0]}{route[1]}")
        return {
            "kind": "flight", "origin": route[0], "destination": route[1],
            "depart_date": depart.date().isoformat(), "return_date": ret.date().isoformat(),
            "target_price": target or round(base * 0.9, 2), "base_price": base,
            "title": f"{route[0]} → {route[1]}", "cabin": "economy",
        }
    checkin = dates[0] if dates else datetime.now(timezone.utc) + timedelta(days=20)
    checkout = dates[1] if len(dates) > 1 else checkin + timedelta(days=3)
    base = _estimate_base("hotel", city or "hotel")
    return {
        "kind": "hotel", "hotel_name": city, "city": city,
        "checkin": checkin.date().isoformat(), "checkout": checkout.date().isoformat(),
        "guests": 2, "rooms": 1, "target_price": target or round(base * 0.9, 2),
        "base_price": base, "title": f"Hotel em {city}",
    }


def _find_watch(norm: str) -> dict | None:
    route = _extract_route(norm)
    watches = db.list_watches()
    if route:
        for w in watches:
            if w["kind"] == "flight" and w["origin"] == route[0] and w["destination"] == route[1]:
                return w
    city = _extract_city(norm)
    if city:
        for w in watches:
            if w["kind"] == "hotel" and city.lower() in (w["city"] or "").lower():
                return w
    for w in watches:
        if _norm(w["title"]) in norm:
            return w
    return None


def _answer_watch(watch: dict) -> str:
    from agent import analyze  # auto-import local

    a = analyze(watch)
    if a.get("current") is None:
        return f"Não tenho preços coletados para {watch['title']} ainda. Execute uma checagem."
    target = a.get("target")
    target_line = (
        f"Seu alvo é {_money(target, a['currency'])}: faltam {_money(a['gap_to_target'], a['currency'])}."
        if target and a.get("gap_to_target", 0) > 0
        else f"Está no/abaixo do alvo de {_money(target, a['currency'])}." if target else "Sem preço-alvo definido."
    )
    return (
        f"{watch['title']}\n"
        f"• Preço atual: {_money(a['current'], a['currency'])}/{a['unit']} "
        f"({a['change_pct']:+.1f}% na última coleta)\n"
        f"• Média histórica: {_money(a['average'], a['currency'])} · mínimo: {_money(a['low'], a['currency'])}\n"
        f"• Recomendação: {a['label']} (confiança {a['confidence']}%)\n"
        f"• {target_line}\n"
        f"• Próxima checagem agendada automaticamente pelo intervalo do watchlist."
    )


def chat(message: str) -> dict:
    from engine import run_check_all

    text = (message or "").strip()
    if not text:
        return {"answer": "Escreva o que você quer monitorar.", "actions": []}
    norm = _norm(text)
    actions: list[str] = []

    if any(k in norm for k in ["rodar", "executar", "checar agora", "checar", "buscar agora", "atualizar agora", "run check", "verificar agora"]):
        result = run_check_all(force=True)
        actions.append("run_check_all")
        return {
            "answer": (
                f"Checagem concluída: {result['checked']} watchlist(s) atualizado(s), "
                f"{result['alerts']} alerta(s) gerado(s)"
                + (f", {result['errors']} erro(s)" if result["errors"] else "")
                + ". Os preços já estão no painel."
            ),
            "actions": actions,
        }

    if any(k in norm for k in ["alerta", "notifica", "aviso"]):
        alerts = db.list_alerts(limit=6)
        actions.append("list_alerts")
        if not alerts:
            return {"answer": "Nenhum alerta no momento. Quando um preço cruzar o alvo ou cair mais de 5%, eu aviso aqui.", "actions": actions}
        lines = ["• " + a["message"] for a in alerts]
        return {"answer": "Alertas recentes:\n" + "\n".join(lines), "actions": actions}

    add_keywords = any(k in norm for k in ["monitor", "acompanh", "rastre", "observar", "vigiar", "watch", "track"])
    parsed = _parse_new_watch(text) if add_keywords else None
    if parsed:
        watch = db.create_watch(parsed)
        from engine import run_check

        result = run_check(watch["id"], force=True)
        actions.extend(["create_watch", "run_check"])
        price = result.get("price")
        return {
            "answer": (
                f"Pronto! Estou monitorando {watch['title']}"
                + (f" no valor de {_money(price, watch['currency'])}/{UNIT[watch['kind']]}" if price else "")
                + f". Alvo definido em {_money(watch['target_price'], watch['currency'])}."
                f" Vou checar a cada {watch['interval_minutes']} minutos e te avisar quando o preço cruzar o alvo."
            ),
            "actions": actions,
            "watch_id": watch["id"],
        }

    if any(k in norm for k in ["quanto", "preco", "valor", "custa", "price", "como esta"]):
        watch = _find_watch(norm)
        if watch:
            actions.append("get_price")
            return {"answer": _answer_watch(watch), "actions": actions}

    if any(k in norm for k in ["briefing", "resumo", "recomend", "oportunidade", "melhor momento", "vale a pena"]):
        briefing = build_briefing()
        actions.append("briefing")
        return {"answer": briefing["text"], "actions": actions, "briefing": briefing}

    help_text = (
        "Posso cuidar do seu monitoramento de viagens. Experimente:\n"
        "• “Monitore THE → LIS em 15/12, abaixo de R$ 4.300”\n"
        "• “Monitore hotel em Lisboa de 10/01 a 14/01 até R$ 700”\n"
        "• “Quanto está Teresina → Lisboa?”\n"
        "• “Rodar checagem agora”\n"
        "• “Me mostre os alertas”\n"
        "• “Faça um briefing das oportunidades”"
    )
    if llm_configured():
        context = json.dumps(
            {
                "watches": [
                    {"titulo": w["title"], "tipo": w["kind"], "preco_atual": analyze(w).get("current"),
                     "alvo": w["target_price"], "moeda": w["currency"]}
                    for w in db.list_watches()
                ],
                "alertas": [a["message"] for a in db.list_alerts(limit=5)],
            },
            ensure_ascii=False,
        )
        system = (
            "Você é o TripWatch Agent, assistente de monitoramento de voos e hotéis. "
            "Responda em português do Brasil, de forma objetiva, usando apenas o contexto fornecido. "
            "Se o usuário pedir para monitorar algo, oriente-o a usar o formulário do painel ou o comando 'Monitore ...'."
        )
        answer = llm_complete(system, f"Contexto:\n{context}\n\nPergunta: {text}", max_tokens=450)
        if answer:
            actions.append("llm")
            return {"answer": answer, "actions": actions, "llm": True}

    return {"answer": help_text, "actions": ["help"]}


def agent_context() -> dict:
    watches = db.list_watches()
    return {
        "agent": db.get_setting("agent_name", "TripWatch Agent"),
        "provider": "demo/serpapi",
        "watches": [
            {
                "id": w["id"], "title": w["title"], "kind": w["kind"],
                "target": w["target_price"], "currency": w["currency"],
                "interval_minutes": w["interval_minutes"], "active": bool(w["active"]),
                "analysis": analyze(w),
            }
            for w in watches
        ],
        "alerts": db.list_alerts(limit=10),
        "briefing": build_briefing(),
    }
