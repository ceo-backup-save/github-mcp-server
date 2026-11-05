/* TripWatch AI — painel (vanilla JS, sem dependências) */
const state = {
  view: "dashboard",
  data: null,
  chat: [],
  chatBusy: false,
  addKind: "flight",
  loading: false,
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const ICONS = {
  plane: '<path d="M17.8 19.2 16 11l3.5-3.5a2.1 2.1 0 0 0-3-3L13 8 4.8 6.2a1 1 0 0 0-.9 1.7l5.6 3.4-2.2 2.2-2.3-.5a.8.8 0 0 0-.7 1.3l2.3 2.3 2.3 2.3a.8.8 0 0 0 1.3-.7l-.5-2.3 2.2-2.2 3.4 5.6a1 1 0 0 0 1.7-.9Z"/>',
  bed: '<path d="M3 18V7"/><path d="M3 12h18a2 2 0 0 1 2 2v4"/><path d="M3 18h20"/><path d="M7 12V9h5v3"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 3v6h-6"/>',
  pause: '<path d="M9 5v14M15 5v14"/>',
  play: '<path d="m7 4 13 8-13 8V4Z"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  trash: '<path d="M3 6h18M8 6V4h8v2M6 6l1 15h10l1-15M10 11v6M14 11v6"/>',
  sparkles: '<path d="m12 3 1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3Z"/><path d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15Z"/>',
  bell: '<path d="M18 8a6 6 0 1 0-12 0c0 7-3 8-3 8h18s-3-1-3-8"/><path d="M10.3 21a2 2 0 0 0 3.4 0"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  check: '<path d="m5 12 5 5L20 7"/>',
  send: '<path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/>',
  copy: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
  external: '<path d="M15 3h6v6M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  radar: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/><path d="M12 12 19 5"/>',
  wallet: '<path d="M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/><path d="M16 12h4"/>',
  alert: '<path d="M12 3 2 21h20L12 3Z"/><path d="M12 9v5M12 18h.01"/>',
  arrowUp: '<path d="M12 19V5M5 12l7-7 7 7"/>',
  arrowDown: '<path d="M12 5v14M5 12l7 7 7-7"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
};

function icon(name, size = 16) {
  return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[name] || ""}</svg>`;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

const SYMBOLS = { BRL: "R$", USD: "US$", EUR: "€" };
function money(value, currency = "BRL") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return `${SYMBOLS[currency] || ""} ${Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`.trim();
}
const unitOf = (kind) => (kind === "hotel" ? "diária" : "pessoa");

function dateLabel(value, opts = { day: "2-digit", month: "short" }) {
  if (!value) return "—";
  const iso = String(value).length <= 10 ? `${value}T12:00:00Z` : value;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("pt-BR", { ...opts, timeZone: "UTC" });
}
function dateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}
function timeAgo(value) {
  if (!value) return "nunca";
  const diff = Math.max(0, Date.now() - new Date(value).getTime());
  const min = Math.floor(diff / 60000);
  if (min < 1) return "agora";
  if (min < 60) return `há ${min} min`;
  const hours = Math.floor(min / 60);
  if (hours < 24) return `há ${hours} h`;
  const days = Math.floor(hours / 24);
  return `há ${days} d`;
}
function countdown(value) {
  if (!value) return "—";
  const diff = new Date(value).getTime() - Date.now();
  if (diff <= 0) return "vencido";
  const min = Math.floor(diff / 60000);
  if (min < 60) return `em ${min} min`;
  const hours = Math.floor(min / 60);
  const rest = min % 60;
  return `em ${hours} h${rest ? ` ${rest} min` : ""}`;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const text = await response.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = {}; }
  if (!response.ok) throw new Error(data.error || `Falha na requisição (${response.status})`);
  return data;
}

function toast(message, type = "success") {
  const root = $("#toast-root");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `${icon(type === "error" ? "alert" : "check", 15)}<span>${esc(message)}</span>`;
  root.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

/* ------------------------------------------------------------------ gráficos */
function sparkline(watch, height = 74) {
  const points = (watch.snapshots || []).slice(-48);
  if (points.length < 2) {
    return `<div class="hint" style="height:${height}px;display:grid;place-items:center">Histórico insuficiente</div>`;
  }
  const prices = points.map((p) => Number(p.price));
  const target = watch.target_price ? Number(watch.target_price) : null;
  const all = target ? [...prices, target] : prices;
  const min = Math.min(...all);
  const max = Math.max(...all);
  const range = max - min || 1;
  const w = 340;
  const h = height;
  const pad = 6;
  const x = (i) => pad + (i * (w - pad * 2)) / (prices.length - 1);
  const y = (v) => h - pad - ((v - min) / range) * (h - pad * 2);
  const line = prices.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p).toFixed(1)}`).join(" ");
  const area = `${line} L${x(prices.length - 1).toFixed(1)},${h - pad} L${x(0).toFixed(1)},${h - pad} Z`;
  const rec = watch.analysis?.recommendation || "watch";
  const color = rec === "buy" ? "#34d399" : rec === "wait" ? "#fbbf24" : "#38bdf8";
  const gid = `grad-${String(watch.id).replace(/[^a-zA-Z0-9]/g, "")}`;
  const lastX = x(prices.length - 1);
  const lastY = y(prices[prices.length - 1]);
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role="img" aria-label="Histórico de preços">
    <defs><linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${color}" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
    </linearGradient></defs>
    ${target ? `<line x1="${pad}" y1="${y(target).toFixed(1)}" x2="${w - pad}" y2="${y(target).toFixed(1)}" stroke="#94a3b8" stroke-opacity="0.45" stroke-width="1" stroke-dasharray="4 4"/>` : ""}
    <path d="${area}" fill="url(#${gid})"/>
    <path d="${line}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${lastX.toFixed(1)}" cy="${lastY.toFixed(1)}" r="3" fill="${color}" stroke="#0b1422" stroke-width="1.5"/>
  </svg>`;
}

/* -------------------------------------------------------------------- pedaços */
function recChip(rec) {
  const map = {
    buy: ["green", "Comprar agora"],
    wait: ["amber", "Aguardar"],
    watch: ["blue", "Observar"],
  };
  const [cls, label] = map[rec] || map.watch;
  return `<span class="chip ${cls}">${label}</span>`;
}

function watchCard(watch) {
  const a = watch.analysis || {};
  const change = Number(a.change_pct || 0);
  const changeCls = change <= -0.05 ? "green" : change >= 0.05 ? "red" : "muted";
  const arrow = change <= -0.05 ? "↓" : change >= 0.05 ? "↑" : "→";
  const isHotel = watch.kind === "hotel";
  const meta = isHotel
    ? `${esc(watch.city || watch.hotel_name || "")} · ${dateLabel(watch.checkin)} → ${dateLabel(watch.checkout)}`
    : `${esc(watch.origin)} → ${esc(watch.destination)} · ${dateLabel(watch.depart_date)}${watch.return_date ? ` → ${dateLabel(watch.return_date)}` : ""}`;
  const paused = !watch.active;
  return `<article class="card watch-card" data-watch="${esc(watch.id)}">
    <div class="watch-top">
      <div class="watch-title">
        <div class="watch-icon ${isHotel ? "hotel" : ""}">${icon(isHotel ? "bed" : "plane", 17)}</div>
        <div style="min-width:0">
          <h3>${esc(watch.title)}</h3>
          <p>${meta}${watch.cabin && watch.cabin !== "economy" ? ` · ${esc(watch.cabin.replace("_", " "))}` : ""}</p>
        </div>
      </div>
      ${paused ? '<span class="chip muted">pausado</span>' : recChip(a.recommendation)}
    </div>
    <div class="watch-price-row">
      <div class="price-big">${money(a.current, watch.currency)}<span> /${unitOf(watch.kind)}</span></div>
      <div class="price-meta">
        <span class="chip ${changeCls}">${arrow} ${Math.abs(change).toFixed(1)}%</span>
        <div>vs. coleta anterior</div>
      </div>
    </div>
    ${sparkline(watch)}
    <div class="watch-stats">
      <div class="stat"><span>Média</span><strong>${money(a.average, watch.currency)}</strong></div>
      <div class="stat"><span>Mínimo</span><strong>${money(a.low, watch.currency)}</strong></div>
      <div class="stat"><span>Alvo</span><strong>${watch.target_price ? money(watch.target_price, watch.currency) : "—"}</strong></div>
    </div>
    <p class="watch-reason">${esc(a.reasons?.[0] || "Sem análise disponível.")}</p>
    <div class="watch-foot">
      <span class="watch-time">${icon("clock", 11)} ${watch.last_checked_at ? timeAgo(watch.last_checked_at) : "nunca checado"}</span>
      <div class="watch-actions">
        <button class="icon-btn" title="Ver detalhes" data-action="detail" data-id="${esc(watch.id)}">${icon("eye", 15)}</button>
        <button class="icon-btn" title="Checar agora" data-action="check" data-id="${esc(watch.id)}">${icon("refresh", 15)}</button>
        <button class="icon-btn" title="${paused ? "Retomar" : "Pausar"}" data-action="toggle" data-id="${esc(watch.id)}">${icon(paused ? "play" : "pause", 15)}</button>
        <button class="icon-btn" title="Editar alvo" data-action="edit-target" data-id="${esc(watch.id)}">${icon("target", 15)}</button>
        <button class="icon-btn danger" title="Excluir" data-action="delete" data-id="${esc(watch.id)}">${icon("trash", 15)}</button>
      </div>
    </div>
  </article>`;
}

function emptyState(title, text, action = "") {
  return `<div class="empty">
    ${icon("radar", 30)}
    <strong>${esc(title)}</strong>
    <p>${esc(text)}</p>
    ${action}
  </div>`;
}

function briefingCard() {
  const briefing = state.data?.briefing;
  if (!briefing) return "";
  const opps = (briefing.opportunities || []).slice(0, 3);
  return `<div class="card briefing">
    <div class="card-head">
      <div>
        <h2>Briefing do agente</h2>
        <p>${esc(state.data.settings.agent_name || "TripWatch Agent")} · ${timeAgo(briefing.generated_at)}</p>
      </div>
      <span class="briefing-badge">${icon("sparkles", 11)} ${briefing.llm ? "LLM" : "análise local"}</span>
    </div>
    <p class="briefing-text">${esc(briefing.text)}</p>
    ${opps.length ? `<div>${opps.map((o) => `<div class="opportunity">
      <span class="dot" style="background:${o.recommendation === "buy" ? "var(--green)" : o.recommendation === "wait" ? "var(--amber)" : "var(--blue)"}"></span>
      <div class="opportunity-main"><strong>${esc(o.title)}</strong><span>${esc(o.label)} · confiança ${o.confidence}%</span></div>
      <div class="opportunity-price">${money(o.current, o.currency)}<small>/${o.unit}</small></div>
    </div>`).join("")}</div>` : ""}
    <div style="display:flex;gap:6px;flex-wrap:wrap">
      <button class="btn btn-ghost btn-sm" data-action="briefing-llm">${icon("sparkles", 13)} Gerar com LLM</button>
      <button class="btn btn-ghost btn-sm" data-action="go-agent">Abrir agente</button>
    </div>
  </div>`;
}

function nextCheckCard() {
  const scheduler = state.data.scheduler;
  const next = scheduler.next_check;
  return `<div class="card">
    <div class="card-head"><div><h2>Próxima checagem</h2><p>agendador automático</p></div>${icon("clock", 16)}</div>
    <div class="kv"><span>Status</span><strong style="color:${scheduler.running ? "var(--green)" : "var(--amber)"}">${scheduler.running ? "ativo" : "parado"}</strong></div>
    <div class="kv"><span>Próxima varredura</span><strong data-countdown="${esc(next?.at || "")}">${next ? countdown(next.at) : "—"}</strong></div>
    <div class="kv"><span>Item</span><strong>${esc(next?.watch || "—")}</strong></div>
    <div class="kv"><span>Intervalo padrão</span><strong>${esc(state.data.settings.check_interval_minutes)} min</strong></div>
    <div class="kv"><span>Checagens na sessão</span><strong>${state.data.stats.snapshots} preços</strong></div>
  </div>`;
}

function providerCard() {
  const provider = state.data.provider;
  return `<div class="card">
    <div class="card-head"><div><h2>Provedor de preços</h2><p>de onde vêm os dados</p></div>${icon("radar", 16)}</div>
    <div class="kv"><span>Provedor ativo</span><strong>${esc(provider.active)}</strong></div>
    <div class="kv"><span>SerpAPI</span><strong>${provider.serpapi_key_present ? "configurada" : "não configurada"}</strong></div>
    <div class="kv"><span>LLM</span><strong>${provider.llm_configured ? "configurado" : "análise local"}</strong></div>
    <p class="hint" style="margin:10px 0 0">${esc(provider.detail)}</p>
    <button class="btn btn-ghost btn-sm" style="margin-top:10px" data-action="go-settings">${icon("settings", 13)} Configurar provedor</button>
  </div>`;
}

function runsCard() {
  const runs = state.data.runs || [];
  return `<div class="card">
    <div class="card-head"><div><h2>Atividade do agente</h2><p>últimas execuções do agendador</p></div>${icon("refresh", 15)}</div>
    ${runs.length ? `<div class="table-wrap"><table class="data">
      <thead><tr><th>Quando</th><th>Status</th><th>Itens</th><th>Alertas</th><th>Log</th></tr></thead>
      <tbody>${runs.map((r) => `<tr>
        <td class="mono">${dateTime(r.finished_at || r.started_at)}</td>
        <td><span class="chip ${r.status === "ok" ? "green" : r.status === "partial" ? "amber" : "muted"}">${esc(r.status)}</span></td>
        <td>${r.checked}</td><td>${r.alerts}</td>
        <td class="mono" style="max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc((r.log || "").slice(0, 90))}</td>
      </tr>`).join("")}</tbody>
    </table></div>` : `<p class="hint">Nenhuma execução registrada ainda.</p>`}
  </div>`;
}

/* ---------------------------------------------------------------------- views */
function kpiCard(cls, label, value, sub, iconName) {
  return `<div class="kpi ${cls}">
    <div class="kpi-label">${icon(iconName, 13)} ${esc(label)}</div>
    <div class="kpi-value">${value}</div>
    <div class="kpi-sub">${sub}</div>
  </div>`;
}

function viewDashboard() {
  const d = state.data;
  const s = d.stats;
  const sorted = [...d.watches].sort((a, b) => {
    const rank = { buy: 0, wait: 1, watch: 2 };
    return (rank[a.analysis?.recommendation] ?? 3) - (rank[b.analysis?.recommendation] ?? 3);
  });
  const top = sorted.slice(0, 3);
  return `<div class="view">
    <div class="kpi-grid">
      ${kpiCard("blue", "Monitorados", `${s.active}<small> / ${s.watches}</small>`, `${s.flights} voos · ${s.hotels} hotéis`, "radar")}
      ${kpiCard("green", "Economia potencial", money(s.potential_savings, s.currency), "soma das diferenças até o alvo", "wallet")}
      ${kpiCard("amber", "No preço-alvo", String(s.below_target), "itens prontos para comprar", "target")}
      ${kpiCard("violet", "Alertas não lidos", String(s.unread_alerts), "notificações do agente", "bell")}
    </div>
    <div class="grid-2">
      <div class="stack">
        <div class="section-title"><h2>Radar de oportunidades</h2><span>ordenado pelo agente · ${top.length} de ${d.watches.length}</span></div>
        ${top.length ? `<div class="watch-grid">${top.map(watchCard).join("")}</div>` : emptyState("Nenhum item monitorado", "Adicione um voo ou hotel para começar a receber o radar de preços.", `<button class="btn btn-primary btn-sm" style="margin-top:6px" data-action="add">${icon("sparkles", 13)} Monitorar agora</button>`)}
        ${runsCard()}
      </div>
      <div class="stack">
        ${briefingCard()}
        ${nextCheckCard()}
        ${providerCard()}
      </div>
    </div>
  </div>`;
}

function viewList(kind) {
  const d = state.data;
  const items = d.watches.filter((w) => w.kind === kind);
  const isFlight = kind === "flight";
  const withData = items.filter((w) => w.analysis?.current);
  const best = withData.length ? Math.min(...withData.map((w) => w.analysis.current)) : null;
  const avg = withData.length ? withData.reduce((sum, w) => sum + w.analysis.average, 0) / withData.length : null;
  return `<div class="view">
    <div class="kpi-grid cols-3">
      ${kpiCard("blue", isFlight ? "Voos monitorados" : "Hotéis monitorados", String(items.length), `${items.filter((w) => w.active).length} ativos`, isFlight ? "plane" : "bed")}
      ${kpiCard("green", "Melhor preço atual", best !== null ? money(best, d.stats.currency) : "—", "menor valor entre os itens", "wallet")}
      ${kpiCard("amber", "Média do radar", avg !== null ? money(avg, d.stats.currency) : "—", "média histórica dos itens", "radar")}
    </div>
    <div class="section-title"><h2>${isFlight ? "Voos" : "Hotéis"} monitorados</h2><span>${items.length} watchlist(s)</span></div>
    ${items.length ? `<div class="watch-grid">${items.map(watchCard).join("")}</div>` : emptyState(
      isFlight ? "Nenhum voo monitorado" : "Nenhum hotel monitorado",
      isFlight ? "Rastreie rotas e receba alertas quando a tarifa cair." : "Acompanhe diárias e reserve no melhor momento.",
      `<button class="btn btn-primary btn-sm" style="margin-top:6px" data-action="add" data-kind="${kind}">${icon("sparkles", 13)} Adicionar ${isFlight ? "voo" : "hotel"}</button>`,
    )}
  </div>`;
}

function viewAgent() {
  const d = state.data;
  const tools = ["search_flights", "search_hotels", "track_flight", "track_hotel", "list_watchlist", "get_price_history", "run_check", "travel_briefing", "list_alerts", "update_target", "delete_watch", "agent_chat"];
  return `<div class="view">
    <div class="grid-2">
      <div class="card chat-card">
        <div class="chat-head">
          <div class="avatar">${icon("sparkles", 17)}</div>
          <div style="flex:1"><strong>${esc(d.settings.agent_name || "TripWatch Agent")}</strong><span>online · conectado às ferramentas do TripWatch</span></div>
          <span class="chip green">${d.provider.llm_configured ? "LLM + local" : "raciocínio local"}</span>
        </div>
        <div class="chat-body" id="chat-body"></div>
        <div class="chat-suggestions">
          <button class="suggestion" data-suggestion="Monitore THE → LIS em 15/12, abaixo de R$ 4.300">Monitore THE → LIS em 15/12, abaixo de R$ 4.300</button>
          <button class="suggestion" data-suggestion="Monitore hotel em Lisboa de 10/01 a 14/01 até R$ 700">Monitore hotel em Lisboa até R$ 700</button>
          <button class="suggestion" data-suggestion="Rodar checagem agora">Rodar checagem agora</button>
          <button class="suggestion" data-suggestion="Faça um briefing das oportunidades">Briefing das oportunidades</button>
        </div>
        <div class="chat-input-row">
          <textarea class="chat-input" id="chat-input" rows="1" placeholder="Peça para monitorar, consultar preços ou rodar checagens…"></textarea>
          <button class="btn btn-primary" id="chat-send" aria-label="Enviar">${icon("send", 15)}</button>
        </div>
      </div>
      <div class="stack">
        ${briefingCard()}
        <div class="card">
          <div class="card-head"><div><h2>Ferramentas do agente</h2><p>expostas via MCP</p></div>${icon("external", 15)}</div>
          <div class="tool-list">${tools.map((t) => `<code>${t}</code>`).join("")}</div>
          <p class="hint" style="margin:10px 0 0">O agente consulta o histórico, cria watchlists, roda checagens e atualiza alvos. Tudo com registro no banco local.</p>
        </div>
        <div class="card">
          <div class="card-head"><div><h2>Como a recomendação é calculada</h2><p>regras + dados históricos</p></div></div>
          <div class="kv"><span>1. Posição vs. média</span><strong>30 dias</strong></div>
          <div class="kv"><span>2. Distância do alvo</span><strong>regra de compra</strong></div>
          <div class="kv"><span>3. Tendência</span><strong>7 dias + inclinação</strong></div>
          <div class="kv"><span>4. Volatilidade</span><strong>confiança</strong></div>
          <p class="hint" style="margin:10px 0 0">Com uma chave de LLM configurada, o briefing ganha linguagem natural sem perder os números do histórico.</p>
        </div>
      </div>
    </div>
  </div>`;
}

function viewAlerts() {
  const alerts = state.data.alerts || [];
  const unread = state.data.stats.unread_alerts;
  return `<div class="view">
    <div class="section-title">
      <h2>Alertas de preço</h2>
      <div style="display:flex;gap:6px">
        ${unread ? `<button class="btn btn-ghost btn-sm" data-action="read-all">${icon("check", 13)} Marcar todos como lidos</button>` : ""}
        <button class="btn btn-ghost btn-sm" data-action="check-all">${icon("refresh", 13)} Checar agora</button>
      </div>
    </div>
    ${alerts.length ? `<div class="alert-list">${alerts.map((a) => {
      const cls = a.kind === "target" ? "target" : a.kind === "drop" ? "drop" : "rise";
      const iconName = a.kind === "target" ? "target" : a.kind === "drop" ? "arrowDown" : "arrowUp";
      return `<div class="alert-row ${a.read_at ? "" : "unread"}">
        <div class="alert-icon ${cls}">${icon(iconName, 15)}</div>
        <div class="alert-main">
          <strong>${esc(a.title)} ${a.read_at ? "" : '<span class="chip green" style="margin-left:6px">novo</span>'}</strong>
          <p>${esc(a.message)}</p>
        </div>
        <div class="alert-time">${timeAgo(a.created_at)}${a.price ? `<br><strong style="color:var(--text)">${money(a.price)}</strong>` : ""}</div>
      </div>`;
    }).join("")}</div>` : emptyState("Tudo tranquilo", "Nenhum alerta ainda. O agente avisa quando o preço cruzar o alvo ou variar mais de 5% entre coletas.")}
  </div>`;
}

function viewSettings() {
  const d = state.data;
  const s = d.settings;
  const mcpUrl = `${location.origin}/mcp`;
  const snippet = `{
  "mcpServers": {
    "tripwatch": {
      "type": "http",
      "url": "${mcpUrl}"
    }
  }
}`;
  return `<div class="view">
    <div class="grid-2">
      <div class="stack">
        <div class="card">
          <div class="card-head"><div><h2>Preferências do monitoramento</h2><p>aplicadas a novos watchlists</p></div>${icon("settings", 15)}</div>
          <div class="form-grid">
            <div class="field"><label for="set-interval">Intervalo de checagem (min)</label><input id="set-interval" type="number" min="15" step="15" value="${esc(s.check_interval_minutes)}" /><small>Executado pelo agendador em segundo plano.</small></div>
            <div class="field"><label for="set-currency">Moeda</label><select id="set-currency"><option value="BRL" ${s.currency === "BRL" ? "selected" : ""}>BRL — Real</option><option value="USD" ${s.currency === "USD" ? "selected" : ""}>USD — Dólar</option><option value="EUR" ${s.currency === "EUR" ? "selected" : ""}>EUR — Euro</option></select></div>
            <div class="field"><label for="set-drop">Alerta de queda (%)</label><input id="set-drop" type="number" min="1" max="50" value="${esc(s.alert_drop_pct)}" /><small>Gera alerta quando a variação entre coletas for maior que isso.</small></div>
            <div class="field"><label for="set-agent">Nome do agente</label><input id="set-agent" type="text" value="${esc(s.agent_name)}" /></div>
            <div class="field full"><label for="set-webhook">Webhook de alertas (opcional)</label><input id="set-webhook" type="url" placeholder="https://api.telegram.org/bot…/sendMessage ou Slack" value="${esc(s.webhook_url)}" /><small>Endpoint que recebe o JSON do alerta. Deixe vazio para manter os alertas no painel.</small></div>
          </div>
          <div class="modal-actions"><button class="btn btn-primary" data-action="save-settings">${icon("check", 14)} Salvar preferências</button></div>
        </div>

        <div class="card">
          <div class="card-head"><div><h2>Provedor de preços</h2><p>dados reais ou simulador</p></div>${icon("radar", 15)}</div>
          <div class="kv"><span>Provedor ativo</span><strong>${esc(d.provider.active)}</strong></div>
          <div class="kv"><span>SerpAPI</span><strong>${d.provider.serpapi_key_present ? "configurada" : "não configurada"}</strong></div>
          <div class="kv"><span>LLM</span><strong>${d.provider.llm_configured ? "configurado" : "não configurado"}</strong></div>
          <p class="hint" style="margin:10px 0 0">${esc(d.provider.detail)}</p>
          <div class="code-block" style="margin-top:10px"># Google Flights + Hotels reais
SERPAPI_KEY=sua_chave
# Opcional: cérebro do briefing
OPENAI_API_KEY=sk-...
# ou ANTHROPIC_API_KEY=sk-ant-...</div>
          <p class="hint" style="margin:8px 0 0">Sem chave, o TripWatch usa um simulador determinístico para você validar o fluxo completo de graça.</p>
        </div>

        <div class="card danger-zone">
          <div class="card-head"><div><h2>Zona de risco</h2><p>ações irreversíveis</p></div>${icon("alert", 15)}</div>
          <p class="hint" style="margin:0 0 10px">Recria o banco com os dados de demonstração. Watchlists, históricos e alertas atuais serão apagados.</p>
          <button class="btn btn-danger btn-sm" data-action="reset-demo">${icon("trash", 13)} Restaurar dados de demonstração</button>
        </div>
      </div>

      <div class="stack">
        <div class="card">
          <div class="card-head"><div><h2>Conectar no Arena / MCP</h2><p>servidor pronto em /mcp</p></div><span class="chip green">online</span></div>
          <p class="hint" style="margin:0 0 8px">Use esta URL como servidor MCP remoto (Streamable HTTP, JSON-RPC 2.0):</p>
          <div class="code-block">${esc(mcpUrl)}<button class="btn btn-ghost btn-sm copy-btn" data-copy="${esc(mcpUrl)}">${icon("copy", 12)}</button></div>
          <p class="hint" style="margin:10px 0 6px">Configuração equivalente para Claude Desktop / Cursor:</p>
          <div class="code-block">${esc(snippet)}<button class="btn btn-ghost btn-sm copy-btn" data-copy="${esc(snippet)}">${icon("copy", 12)}</button></div>
          <div class="tool-list" style="margin-top:10px">${["search_flights", "search_hotels", "track_flight", "track_hotel", "run_check", "travel_briefing", "agent_chat"].map((t) => `<code>${t}</code>`).join("")}</div>
        </div>

        <div class="card">
          <div class="card-head"><div><h2>Agendador</h2><p>checagens em segundo plano</p></div>${icon("clock", 15)}</div>
          <div class="kv"><span>Status</span><strong style="color:${d.scheduler.running ? "var(--green)" : "var(--amber)"}">${d.scheduler.running ? "ativo" : "parado"}</strong></div>
          <div class="kv"><span>Próxima checagem</span><strong data-countdown="${esc(d.scheduler.next_check?.at || "")}">${d.scheduler.next_check ? countdown(d.scheduler.next_check.at) : "—"}</strong></div>
          <div class="kv"><span>Item prioritário</span><strong>${esc(d.scheduler.next_check?.watch || "—")}</strong></div>
          <div class="kv"><span>Tick do loop</span><strong>${d.scheduler.tick_seconds}s</strong></div>
          <div class="kv"><span>Preços no histórico</span><strong>${d.stats.snapshots}</strong></div>
        </div>

        <div class="card">
          <div class="card-head"><div><h2>Arquitetura</h2><p>sem dependências externas</p></div>${icon("radar", 15)}</div>
          <div class="kv"><span>Servidor</span><strong>Python stdlib</strong></div>
          <div class="kv"><span>Banco</span><strong>SQLite (WAL)</strong></div>
          <div class="kv"><span>Agendador</span><strong>thread em processo</strong></div>
          <div class="kv"><span>Provedores</span><strong>demo · SerpAPI</strong></div>
          <div class="kv"><span>Agente</span><strong>regras + LLM opcional</strong></div>
          <div class="kv"><span>Interface</span><strong>HTML/CSS/JS puro</strong></div>
        </div>
      </div>
    </div>
  </div>`;
}

function renderView() {
  const root = $("#view-root");
  if (!state.data) {
    root.innerHTML = `<div class="view"><div class="card"><p class="hint">Carregando radar…</p></div></div>`;
    return;
  }
  const views = {
    dashboard: viewDashboard,
    flights: () => viewList("flight"),
    hotels: () => viewList("hotel"),
    agent: viewAgent,
    alerts: viewAlerts,
    settings: viewSettings,
  };
  root.innerHTML = (views[state.view] || viewDashboard)();
  if (state.view === "agent") renderChat();
}

function renderChrome() {
  const d = state.data;
  $$(".nav-item").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === state.view));
  const titles = {
    dashboard: ["Painel", "Radar de preços de voos e hotéis com agentes de IA."],
    flights: ["Voos", "Rotas monitoradas, histórico de tarifas e alertas de queda."],
    hotels: ["Hotéis", "Diárias monitoradas com preço-alvo e recomendação de compra."],
    agent: ["Agente IA", "Converse, crie monitoramentos e peça análises em linguagem natural."],
    alerts: ["Alertas", "Tudo o que o agente detectou de relevante."],
    settings: ["Configurações", "Provedor, agendador, MCP e preferências."],
  };
  const [title, subtitle] = titles[state.view] || titles.dashboard;
  $("#page-title").textContent = title;
  $("#page-subtitle").textContent = subtitle;
  if (!d) return;
  $("#count-flights").textContent = d.stats.flights;
  $("#count-hotels").textContent = d.stats.hotels;
  const badge = $("#count-alerts");
  badge.textContent = d.stats.unread_alerts;
  badge.classList.toggle("zero", d.stats.unread_alerts === 0);
  const dot = $("#scheduler-dot");
  dot.classList.toggle("off", !d.scheduler.running);
  dot.classList.toggle("pulse", d.scheduler.running);
  $("#scheduler-label").textContent = d.scheduler.running ? "Agendador ativo" : "Agendador parado";
  $("#next-check-label").textContent = d.scheduler.next_check
    ? `Próxima: ${d.scheduler.next_check.watch} · ${countdown(d.scheduler.next_check.at)}`
    : "Sem checagens pendentes";
  $("#provider-label").textContent = `preços: ${d.provider.active}${d.provider.serpapi_key_present ? " · serpapi" : " · demo"}`;
}

/* ----------------------------------------------------------------------- chat */
function initialChat() {
  const name = state.data?.settings?.agent_name || "TripWatch Agent";
  return [{
    role: "assistant",
    text: `Olá! Sou o ${name}. Posso monitorar voos e hotéis, consultar preços, rodar checagens e explicar o histórico.\n\nExemplos:\n• Monitore THE → LIS em 15/12, abaixo de R$ 4.300\n• Monitore hotel em Lisboa de 10/01 a 14/01 até R$ 700\n• Quanto está Teresina → Lisboa?\n• Rodar checagem agora`,
    actions: [],
  }];
}

function renderChat() {
  const body = $("#chat-body");
  if (!body) return;
  if (!state.chat.length) state.chat = initialChat();
  body.innerHTML = state.chat.map((m) => `<div class="msg ${m.role}">
    <div class="msg-bubble">${esc(m.text)}</div>
    ${m.actions && m.actions.length ? `<div class="msg-actions">${m.actions.map((a) => `<span class="chip violet">${esc(a)}</span>`).join("")}</div>` : ""}
  </div>`).join("") + (state.chatBusy ? `<div class="msg assistant"><div class="msg-bubble"><span class="typing"><i></i><i></i><i></i></span></div></div>` : "");
  body.scrollTop = body.scrollHeight;
}

async function sendChat(text) {
  const message = (text ?? $("#chat-input")?.value ?? "").trim();
  if (!message || state.chatBusy) return;
  if (!state.chat.length) state.chat = initialChat();
  state.chat.push({ role: "user", text: message });
  const input = $("#chat-input");
  if (input) { input.value = ""; input.style.height = "auto"; }
  state.chatBusy = true;
  renderChat();
  try {
    const response = await api("/api/agent/chat", { method: "POST", body: JSON.stringify({ message }) });
    state.chat.push({ role: "assistant", text: response.answer, actions: response.actions || [] });
    if ((response.actions || []).some((a) => ["create_watch", "run_check", "run_check_all"].includes(a))) {
      await load();
    }
  } catch (error) {
    state.chat.push({ role: "assistant", text: `Não consegui executar: ${error.message}` });
  } finally {
    state.chatBusy = false;
    renderChat();
  }
}

/* --------------------------------------------------------------------- modais */
function openModal(html, wide = false) {
  $("#modal-root").innerHTML = `<div class="modal-backdrop" data-close="1"><div class="modal ${wide ? "wide" : ""}" role="dialog" aria-modal="true">${html}</div></div>`;
  document.body.style.overflow = "hidden";
}
function closeModal() {
  $("#modal-root").innerHTML = "";
  document.body.style.overflow = "";
}

function addFormFields(kind) {
  if (kind === "flight") {
    return `<div class="form-grid">
      <div class="field"><label>Origem (IATA)</label><input name="origin" maxlength="3" placeholder="THE" required /></div>
      <div class="field"><label>Destino (IATA)</label><input name="destination" maxlength="3" placeholder="LIS" required /></div>
      <div class="field"><label>Ida</label><input name="depart_date" type="date" required /></div>
      <div class="field"><label>Volta (opcional)</label><input name="return_date" type="date" /></div>
      <div class="field"><label>Cabine</label><select name="cabin"><option value="economy">Econômica</option><option value="premium_economy">Premium econômica</option><option value="business">Executiva</option><option value="first">Primeira</option></select></div>
      <div class="field"><label>Preço-alvo (R$)</label><input name="target_price" type="number" min="1" step="0.01" placeholder="4300" /></div>
    </div>`;
  }
  return `<div class="form-grid">
    <div class="field"><label>Cidade</label><input name="city" placeholder="Lisboa" required /></div>
    <div class="field"><label>Hotel (opcional)</label><input name="hotel_name" placeholder="Memmo Alfama" /></div>
    <div class="field"><label>Check-in</label><input name="checkin" type="date" required /></div>
    <div class="field"><label>Check-out</label><input name="checkout" type="date" required /></div>
    <div class="field"><label>Hóspedes</label><input name="guests" type="number" min="1" value="2" /></div>
    <div class="field"><label>Quartos</label><input name="rooms" type="number" min="1" value="1" /></div>
    <div class="field full"><label>Preço-alvo por diária (R$)</label><input name="target_price" type="number" min="1" step="0.01" placeholder="700" /></div>
  </div>`;
}

function openAddModal(kind = "flight") {
  state.addKind = kind;
  const today = new Date();
  const plus = (days) => new Date(today.getTime() + days * 86400000).toISOString().slice(0, 10);
  openModal(`<div class="modal-head">
      <div><h2>Monitorar novo ${kind === "flight" ? "voo" : "hotel"}</h2><p>O agente coleta o preço e compara com o histórico.</p></div>
      <button class="modal-close" data-close="1" aria-label="Fechar">✕</button>
    </div>
    <form id="add-form" novalidate>
      <div class="segmented" style="margin-bottom:14px">
        <button type="button" class="${kind === "flight" ? "active" : ""}" data-action="set-add-kind" data-kind="flight">✈ Voo</button>
        <button type="button" class="${kind === "hotel" ? "active" : ""}" data-action="set-add-kind" data-kind="hotel">🛏 Hotel</button>
      </div>
      <div id="add-fields">${addFormFields(kind)}</div>
      <div class="form-grid" style="margin-top:12px">
        <div class="field"><label>Intervalo de checagem</label><select name="interval_minutes"><option value="60">A cada 1 hora</option><option value="180" selected>A cada 3 horas</option><option value="360">A cada 6 horas</option><option value="720">A cada 12 horas</option><option value="1440">A cada 24 horas</option></select></div>
        <div class="field"><label>Moeda</label><select name="currency"><option value="BRL">BRL — Real</option><option value="USD">USD — Dólar</option><option value="EUR">EUR — Euro</option></select></div>
      </div>
      <p class="hint" style="margin:10px 0 0">Sem chave de provedor, o primeiro preço vem do simulador determinístico — o restante do fluxo (histórico, alertas, agente e MCP) é real.</p>
      <div class="form-error" id="add-error"></div>
      <div class="modal-actions">
        <button type="button" class="btn btn-ghost" data-close="1">Cancelar</button>
        <button type="submit" class="btn btn-primary">${icon("sparkles", 14)} Começar a monitorar</button>
      </div>
    </form>`);
  const form = $("#add-form");
  if (form) {
    form.addEventListener("submit", submitAddForm);
    const dateInputs = $$('input[type="date"]', form);
    if (dateInputs[0]) dateInputs[0].value = plus(30);
    if (dateInputs[1]) dateInputs[1].value = plus(37);
  }
}

async function submitAddForm(event) {
  event.preventDefault();
  const form = event.target;
  const fd = new FormData(form);
  const kind = state.addKind;
  const payload = {
    kind,
    interval_minutes: Number(fd.get("interval_minutes") || 180),
    currency: fd.get("currency") || "BRL",
    target_price: fd.get("target_price") ? Number(fd.get("target_price")) : null,
  };
  const errorEl = $("#add-error");
  if (kind === "flight") {
    payload.origin = (fd.get("origin") || "").trim().toUpperCase();
    payload.destination = (fd.get("destination") || "").trim().toUpperCase();
    payload.depart_date = fd.get("depart_date");
    payload.return_date = fd.get("return_date") || null;
    payload.cabin = fd.get("cabin") || "economy";
    if (!payload.origin || !payload.destination || !payload.depart_date) {
      errorEl.textContent = "Preencha origem, destino e data de ida.";
      return;
    }
  } else {
    payload.city = (fd.get("city") || "").trim();
    payload.hotel_name = (fd.get("hotel_name") || "").trim() || null;
    payload.checkin = fd.get("checkin");
    payload.checkout = fd.get("checkout");
    payload.guests = Number(fd.get("guests") || 1);
    payload.rooms = Number(fd.get("rooms") || 1);
    if (!payload.city || !payload.checkin || !payload.checkout) {
      errorEl.textContent = "Preencha cidade, check-in e check-out.";
      return;
    }
  }
  const submit = form.querySelector('button[type="submit"]');
  if (submit) { submit.disabled = true; submit.textContent = "Coletando preço…"; }
  try {
    await api("/api/watches", { method: "POST", body: JSON.stringify(payload) });
    closeModal();
    toast(`${payload.origin ? `${payload.origin} → ${payload.destination}` : payload.city} agora está no radar.`);
    await load();
  } catch (error) {
    errorEl.textContent = error.message;
    if (submit) { submit.disabled = false; submit.innerHTML = `${icon("sparkles", 14)} Começar a monitorar`; }
  }
}

function openDetail(id) {
  const watch = state.data.watches.find((w) => w.id === id);
  if (!watch) return;
  const a = watch.analysis || {};
  const history = [...(watch.snapshots || [])].slice(-12).reverse();
  openModal(`<div class="modal-head">
      <div><h2>${esc(watch.title)}</h2><p>${watch.kind === "flight" ? `${esc(watch.origin)} → ${esc(watch.destination)} · ${dateLabel(watch.depart_date)}` : `${esc(watch.city || watch.hotel_name)} · ${dateLabel(watch.checkin)} → ${dateLabel(watch.checkout)}`}</p></div>
      <button class="modal-close" data-close="1" aria-label="Fechar">✕</button>
    </div>
    <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:10px;margin-bottom:6px">
      <div><div class="price-big" style="font-size:30px">${money(a.current, watch.currency)}<span> /${unitOf(watch.kind)}</span></div>
      <div class="hint">${a.points || 0} coletas · confiança ${a.confidence || 0}%</div></div>
      ${recChip(a.recommendation)}
    </div>
    ${sparkline(watch, 110)}
    <div class="watch-stats" style="margin-top:10px">
      <div class="stat"><span>Média</span><strong>${money(a.average, watch.currency)}</strong></div>
      <div class="stat"><span>Mínimo</span><strong>${money(a.low, watch.currency)}</strong></div>
      <div class="stat"><span>Alvo</span><strong>${watch.target_price ? money(watch.target_price, watch.currency) : "—"}</strong></div>
    </div>
    <div class="card" style="margin-top:12px;padding:13px;background:rgba(2,6,23,.25)">
      <div class="card-title-row" style="margin-bottom:8px">${icon("sparkles", 14)}<strong style="font-size:12px">Por que essa recomendação?</strong></div>
      <ul style="margin:0;padding-left:16px;font-size:11.5px;line-height:1.7;color:var(--muted)">${(a.reasons || []).map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
    </div>
    <div class="table-wrap" style="margin-top:12px">
      <table class="data"><thead><tr><th>Quando</th><th>Preço</th><th>Provedor</th></tr></thead><tbody>
      ${history.map((s) => `<tr><td class="mono">${dateTime(s.found_at)}</td><td><strong>${money(s.price, s.currency)}</strong></td><td class="mono">${esc(s.provider)}</td></tr>`).join("")}
      </tbody></table>
    </div>
    <div class="modal-actions">
      <button class="btn btn-ghost btn-sm" data-action="edit-target" data-id="${esc(watch.id)}">${icon("target", 13)} Editar alvo</button>
      <button class="btn btn-ghost btn-sm" data-action="check" data-id="${esc(watch.id)}">${icon("refresh", 13)} Checar agora</button>
      <button class="btn btn-danger btn-sm" data-action="delete" data-id="${esc(watch.id)}">${icon("trash", 13)} Excluir</button>
    </div>`, true);
}

function openTargetModal(id) {
  const watch = state.data.watches.find((w) => w.id === id);
  if (!watch) return;
  openModal(`<div class="modal-head">
      <div><h2>Preço-alvo</h2><p>${esc(watch.title)}</p></div>
      <button class="modal-close" data-close="1" aria-label="Fechar">✕</button>
    </div>
    <div class="field"><label for="target-input">Alvo em ${esc(watch.currency)} (${unitOf(watch.kind)})</label>
      <input id="target-input" type="number" min="1" step="0.01" value="${watch.target_price ?? ""}" placeholder="Ex.: 4300" />
      <small>O agente emite alerta quando o preço ficar neste valor ou abaixo.</small>
    </div>
    <div class="modal-actions">
      <button class="btn btn-ghost" data-close="1">Cancelar</button>
      <button class="btn btn-primary" data-action="save-target" data-id="${esc(watch.id)}">${icon("check", 14)} Salvar alvo</button>
    </div>`);
}

function confirmDelete(id) {
  const watch = state.data.watches.find((w) => w.id === id);
  if (!watch) return;
  openModal(`<div class="modal-head">
      <div><h2>Excluir monitoramento?</h2><p>${esc(watch.title)}</p></div>
      <button class="modal-close" data-close="1" aria-label="Fechar">✕</button>
    </div>
    <p class="hint" style="margin:0">O histórico de preços e os alertas deste item serão apagados. A ação não pode ser desfeita.</p>
    <div class="modal-actions">
      <button class="btn btn-ghost" data-close="1">Cancelar</button>
      <button class="btn btn-danger" data-action="confirm-delete" data-id="${esc(watch.id)}">${icon("trash", 14)} Excluir</button>
    </div>`);
}

/* --------------------------------------------------------------------- ações */
async function load() {
  try {
    state.data = await api("/api/state");
    renderChrome();
    renderView();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function checkWatch(id) {
  try {
    const result = await api(`/api/watches/${id}/check`, { method: "POST" });
    toast(`${result.analysis?.title || "Item"}: ${money(result.price, result.currency)} (${result.provider})`);
    await load();
  } catch (error) { toast(error.message, "error"); }
}

async function toggleWatch(id) {
  const watch = state.data.watches.find((w) => w.id === id);
  if (!watch) return;
  try {
    await api(`/api/watches/${id}`, { method: "PATCH", body: JSON.stringify({ active: !watch.active }) });
    toast(watch.active ? "Monitoramento pausado." : "Monitoramento retomado.");
    await load();
  } catch (error) { toast(error.message, "error"); }
}

async function saveTarget(id) {
  const value = $("#target-input")?.value;
  if (!value) { toast("Informe um valor de alvo.", "error"); return; }
  try {
    await api(`/api/watches/${id}`, { method: "PATCH", body: JSON.stringify({ target_price: Number(value) }) });
    closeModal();
    toast("Preço-alvo atualizado.");
    await load();
  } catch (error) { toast(error.message, "error"); }
}

async function deleteWatch(id) {
  try {
    await api(`/api/watches/${id}`, { method: "DELETE" });
    closeModal();
    toast("Monitoramento excluído.");
    await load();
  } catch (error) { toast(error.message, "error"); }
}

async function runAll() {
  const button = $("#check-all-btn");
  if (button) { button.disabled = true; button.textContent = "Checando…"; }
  try {
    const result = await api("/api/check-all", { method: "POST" });
    toast(`${result.checked} item(ns) checado(s), ${result.alerts} alerta(s).`);
    await load();
  } catch (error) { toast(error.message, "error"); }
  finally { if (button) { button.disabled = false; button.innerHTML = `${icon("check", 16)} Checar agora`; } }
}

async function generateBriefing() {
  try {
    toast("Gerando briefing com LLM…");
    const briefing = await api("/api/briefing", { method: "POST", body: JSON.stringify({ use_llm: true }) });
    if (state.data) state.data.briefing = briefing;
    renderView();
    toast(briefing.llm ? "Briefing gerado pelo LLM." : "LLM indisponível; análise local mantida.", briefing.llm ? "success" : "error");
  } catch (error) { toast(error.message, "error"); }
}

async function saveSettings() {
  const payload = {
    check_interval_minutes: $("#set-interval")?.value,
    currency: $("#set-currency")?.value,
    alert_drop_pct: $("#set-drop")?.value,
    agent_name: $("#set-agent")?.value,
    webhook_url: $("#set-webhook")?.value,
  };
  try {
    await api("/api/settings", { method: "POST", body: JSON.stringify({ settings: payload }) });
    toast("Preferências salvas.");
    await load();
  } catch (error) { toast(error.message, "error"); }
}

async function markAllRead() {
  try {
    await api("/api/alerts/read", { method: "POST", body: JSON.stringify({}) });
    toast("Alertas marcados como lidos.");
    await load();
  } catch (error) { toast(error.message, "error"); }
}

async function resetDemo() {
  openModal(`<div class="modal-head">
      <div><h2>Restaurar demonstração?</h2><p>Isso apaga os dados atuais.</p></div>
      <button class="modal-close" data-close="1" aria-label="Fechar">✕</button>
    </div>
    <p class="hint" style="margin:0">Watchlists, históricos, alertas e execuções serão substituídos pelo conjunto de demonstração.</p>
    <div class="modal-actions">
      <button class="btn btn-ghost" data-close="1">Cancelar</button>
      <button class="btn btn-danger" data-action="confirm-reset">${icon("trash", 14)} Restaurar</button>
    </div>`);
}

async function confirmReset() {
  try {
    await api("/api/reset-demo", { method: "POST", body: "{}" });
    closeModal();
    toast("Dados de demonstração restaurados.");
    await load();
  } catch (error) { toast(error.message, "error"); }
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast("Copiado para a área de transferência.");
    return;
  } catch {
    /* fallback para contextos sem clipboard API (http) */
  }
  try {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
    toast("Copiado para a área de transferência.");
  } catch {
    toast("Não foi possível copiar automaticamente.", "error");
  }
}

/* -------------------------------------------------------------------- eventos */
document.addEventListener("click", async (event) => {
  const nav = event.target.closest(".nav-item");
  if (nav) {
    state.view = nav.dataset.view;
    renderChrome();
    renderView();
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }

  const suggestion = event.target.closest("[data-suggestion]");
  if (suggestion) { sendChat(suggestion.dataset.suggestion); return; }

  const copy = event.target.closest("[data-copy]");
  if (copy) { copyText(copy.dataset.copy); return; }

  const closer = event.target.closest("[data-close]");
  if (closer && (closer === event.target || event.target.closest(".modal-close"))) {
    closeModal();
    return;
  }

  const actionEl = event.target.closest("[data-action]");
  if (!actionEl) return;
  const action = actionEl.dataset.action;
  const id = actionEl.dataset.id;

  switch (action) {
    case "add": openAddModal(actionEl.dataset.kind || "flight"); break;
    case "set-add-kind": {
      state.addKind = actionEl.dataset.kind;
      $$("#add-form .segmented button").forEach((b) => b.classList.toggle("active", b.dataset.kind === state.addKind));
      const fields = $("#add-fields");
      if (fields) fields.innerHTML = addFormFields(state.addKind);
      break;
    }
    case "detail": openDetail(id); break;
    case "check": await checkWatch(id); break;
    case "toggle": await toggleWatch(id); break;
    case "edit-target": openTargetModal(id); break;
    case "save-target": await saveTarget(id); break;
    case "delete": confirmDelete(id); break;
    case "confirm-delete": await deleteWatch(id); break;
    case "check-all": await runAll(); break;
    case "briefing-llm": await generateBriefing(); break;
    case "go-agent": state.view = "agent"; renderChrome(); renderView(); break;
    case "go-settings": state.view = "settings"; renderChrome(); renderView(); break;
    case "save-settings": await saveSettings(); break;
    case "read-all": await markAllRead(); break;
    case "reset-demo": await resetDemo(); break;
    case "confirm-reset": await confirmReset(); break;
    default: break;
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeModal();
  if (event.key === "Enter" && event.target.id === "chat-input" && !event.shiftKey) {
    event.preventDefault();
    sendChat();
  }
});

document.addEventListener("input", (event) => {
  if (event.target.id === "chat-input") {
    event.target.style.height = "auto";
    event.target.style.height = `${Math.min(120, event.target.scrollHeight)}px`;
  }
});

document.addEventListener("click", (event) => {
  if (event.target.id === "chat-send") sendChat();
  if (event.target.id === "refresh-btn") load();
  if (event.target.id === "add-btn") openAddModal("flight");
  if (event.target.id === "check-all-btn") runAll();
});

setInterval(() => {
  $$("[data-countdown]").forEach((el) => { el.textContent = countdown(el.dataset.countdown); });
  if (state.data?.scheduler?.next_check) {
    const label = $("#next-check-label");
    if (label) label.textContent = `Próxima: ${state.data.scheduler.next_check.watch} · ${countdown(state.data.scheduler.next_check.at)}`;
  }
}, 30000);

load();
