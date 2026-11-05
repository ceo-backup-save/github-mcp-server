# Repositórios para rastrear voos e hotéis com IA

Levantamento feito em **2026-11-05** via API do GitHub e READMEs dos repositórios.
Estrelas, licenças e datas refletem o momento da consulta.

## TL;DR

| Objetivo | Repositório recomendado |
|---|---|
| **Rodar agora no Arena, sem chave, com MCP e agendador** | **TripWatch AI** (este checkout, `tripwatch/`) |
| **Produto open-source completo, self-hosted, com UI e histórico** | [affromero/flight-finder](https://github.com/affromero/flight-finder) |
| **Agente que pesquisa e também reserva voos/hotéis** | [LetsFG/LetsFG](https://github.com/LetsFG/LetsFG) |
| **Milhas, pontos e award flights** | [borski/travel-hacking-toolkit](https://github.com/borski/travel-hacking-toolkit) |
| **MCP local sem API keys, uso pessoal** | [MikkoParkkola/trvl](https://github.com/MikkoParkkola/trvl) |
| **Referência de agente com Telegram + SerpAPI + Claude** | [ruchirpipalia-spec/travel-agent](https://github.com/ruchirpipalia-spec/travel-agent) |

## Critérios usados

1. **Fonte de preço**: API oficial, scraping ou simulador.
2. **Agendamento**: cron, fila, loop interno ou "só sob demanda".
3. **Agente**: MCP, skills, CLI ou apenas API.
4. **Self-hosting**: Docker/binário/serviço gerenciado.
5. **Licença**: MIT/Apache (permissiveis) vs. custom/não comercial.
6. **Risco jurídico e operacional**: scraping de Google/Booking, ToS, chaves pagas.

## Comparativo

| Repositório | ⭐ | Linguagem | Licença | Fonte de preço | Agendamento | Agente | Self-host |
|---|---:|---|---|---|---|---|---|
| [LetsFG/LetsFG](https://github.com/LetsFG/LetsFG) | ~2.230 | Python | outra (NOASSERTION) | API própria (todas as companhias + OTAs) | no servidor deles | MCP + CLI + SDK Python/JS | não (serviço) |
| [affromero/flight-finder](https://github.com/affromero/flight-finder) | ~183 | TypeScript | MIT | Playwright + extração por LLM | cron a cada 3h | Claude Code/Codex + API | sim (Docker) |
| [borski/travel-hacking-toolkit](https://github.com/borski/travel-hacking-toolkit) | ~888 | Python | MIT | dados de programas de fidelidade | skills | MCP/skills | sim |
| [jeancsil/flight-spy](https://github.com/jeancsil/flight-spy) | ~185 | PHP | MIT | Skyscanner API | sim | API/CLI | sim |
| [saraswatayu/swoop](https://github.com/saraswatayu/swoop) | ~101 | Python | MIT | Google Flights (sem key) | sob demanda | biblioteca | sim |
| [MikkoParkkola/trvl](https://github.com/MikkoParkkola/trvl) | ~93 | Go | PolyForm NC 1.0 | 24 provedores públicos | alertas | MCP (1 tool + aliases) | sim (binário) |
| [flightclaw/agents](https://github.com/flightclaw/agents) | ~82 | Python | MIT | Google Flights + API própria | diário | MCP + skills | sim (local) |
| [mtnrabi/travel-agent-skills](https://github.com/mtnrabi/travel-agent-skills) | ~4 | skills | MIT | RapidAPI (FlightPowers) | fare watch | MCP/skills | sim |
| [ruchirpipalia-spec/travel-agent](https://github.com/ruchirpipalia-spec/travel-agent) | 0 | Python | sem licença | SerpAPI | 24h | Telegram + Claude | sim |
| **TripWatch AI (este repo)** | — | Python | MIT | SerpAPI ou simulador | loop interno por item | MCP + regras + LLM opcional | sim |

> `itai-gendler/flight-finder` é um **fork** de `affromero/flight-finder` com 0 estrelas.
> A fonte canônica é `affromero/flight-finder`.

## Análise por repositório

### 1. LetsFG/LetsFG — o mais "agente de viagem" de ponta a ponta

- **O que faz**: busca de voos e hotéis com preço total, e **booking real** (a tarifa é
  reservada no cartão e um agente do LetsFG compra a passagem; o PNR é devolvido ao usuário).
- **Integração**: MCP em `https://letsfg.co/mcp`, CLI, SDK Python (`pip install letsfg`) e JS.
  Busca gratuita; booking com custo/condições próprias.
- **Pontos fortes**: cobre "todas as companhias", histórico de confiabilidade por voo,
  preço estável em buscas repetidas, pensado para agentes.
- **Atenção**: licença custom (`NOASSERTION`) — leia antes de uso comercial; o booking
  envolve pagamento e dados pessoais; não é self-hosted.
- **Melhor para**: quem quer que o agente **pesquise e reserve** com um único MCP.

### 2. affromero/flight-finder — a melhor base open-source de produto

- **O que faz**: tracking de voos, hotéis e aluguel de carros; histórico em PostgreSQL;
  gráficos; alertas; CLI headless; busca em linguagem natural com LLM; comparação de VPN.
- **Stack**: Next.js 16, Prisma 7, PostgreSQL, Playwright (headless Chromium), Socket,
  Docker. Instalação assistida por `install.sh`.
- **Integração**: API própria + CLI (`flight-finder --headless`), `AGENTS.md` para Claude
  Code/Codex, BYOK (traga suas chaves), LLM 100% local possível.
- **Pontos fortes**: é o mais próximo de um produto completo; cron de 3h; gráficos
  compartilháveis; hotéis e carros no mesmo lugar.
- **Atenção**: scraping de Google Flights/Hotels pode violar termos de uso; requer
  Chromium e mais recursos; complexidade operacional maior.
- **Melhor para**: quem quer **self-hostar um produto sério** e tem Docker/Postgres.

### 3. borski/travel-hacking-toolkit — milhas e pontos

- **O que faz**: skills e MCPs para busca com dinheiro, pontos e milhas, incluindo award
  flights; drop-in para Claude, Codex e OpenCode.
- **Melhor para**: viajantes brasileiros/americanos que querem otimizar programas de
  fidelidade, não apenas o preço em dinheiro.
- **Atenção**: não é um painel de preços; é um toolkit de habilidades.

### 4. jeancsil/flight-spy — simples e direto

- PHP, MIT, usa API do Skyscanner. Bom para alertas de preço sem montar stack.
- **Melhor para**: quem já tem PHP/hosting e quer algo enxuto.

### 5. saraswatayu/swoop — Google Flights sem API key

- Biblioteca Python com resultados tipados e preços reais, sem chave.
- **Atenção**: depende de endpoints não oficiais; pode quebrar sem aviso.
- **Melhor para**: protótipos e uso pessoal.

### 6. MikkoParkkola/trvl — MCP local sem chaves

- Binário Go único, 24 provedores, preço, trens, carros, balsas, clima, alertas.
  MCP 2026-07-28, 1 tool inteligente + aliases.
- **Licença PolyForm NC 1.0**: **não comercial**.
- **Melhor para**: uso pessoal e agentes locais que não podem usar chaves de API.

### 7. flightclaw/agents — tracking diário com e-mail

- MCP hospedado (`mcp.flightclaw.com/mcp`) + servidor local open-source.
- Skills de booking, tracking diário com alerta por e-mail, perfil de viajante.
- **Melhor para**: quem quer booking + tracking com menos infraestrutura.

### 8. mtnrabi/travel-agent-skills — 8 skills prontas

- Skills para datas mais baratas, fare watch, planejamento, busca de hotel e paridade de
  tarifas. Funciona com MCP ou REST, requer RapidAPI.
- **Melhor para**: adicionar capacidades de viagem a um agente já existente.

### 9. ruchirpipalia-spec/travel-agent — referência de agente

- Telegram + Claude + SerpAPI + Supabase; alertas por e-mail; memória de preferências.
- **Sem licença** e sem estrelas: use como **referência arquitetural**, não como dependência.
- **Melhor para**: estudar o padrão "chat → ferramenta → alerta".

## Arquitetura recomendada (a que este projeto implementa)

```
[Cliente: Arena / Claude / Cursor / Web]
        │ MCP (JSON-RPC)
        ▼
[Agente]  planeja, decide e chama ferramentas
        │
        ├──► [Provedor de preço]  SerpAPI · LetsFG · outro MCP
        ├──► [Memória]            SQLite/Postgres com série temporal
        ├──► [Agendador]          checa de 3h em 3h, gera alertas
        └──► [Notificações]       painel · webhook · Telegram · e-mail
```

O erro comum é colocar o LLM como fonte de preço. O LLM deve **interpretar** o histórico e
**escolher ferramentas**; o preço vem de um provedor auditável. O TripWatch segue esse
princípio: `providers.py` coleta, `db.py` guarda, `engine.py` agenda, `agent.py` interpreta.

## Como instalar cada opção

### TripWatch AI (este checkout)

```bash
cd tripwatch
python3 app.py                 # painel + API + MCP em :8787
```

Sem chave, já funciona com o simulador. Para dados reais:

```bash
SERPAPI_KEY=sua_chave python3 app.py
```

Instruções de Arena/MCP: [`ARENA.md`](./ARENA.md).

### affromero/flight-finder

```bash
curl -fsSL https://flight-finder.org/install.sh | bash
```

Requer Docker (Next.js + Postgres + Playwright). Configure o provedor de LLM no setup.
Consulte o README do projeto para a versão atual.

### LetsFG

```bash
pip install letsfg
export LETSFG_API_KEY="token"
```

Ou conecte `https://letsfg.co/mcp` como servidor MCP no cliente. A busca é gratuita;
o booking é cobrado/preparado pelo provedor.

### trvl

Baixe o binário da release e rode:

```bash
trvl mcp        # servidor MCP local
```

Licença não comercial.

## Veredito

Para a pergunta **"existe repositório capaz de executar isso e instalar no próprio Arena?"**:

- **Sim, e você já está nele**: o `tripwatch/` é uma aplicação completa, sem dependências,
  com painel, agendador, agente e **servidor MCP** — pronta para o preview do Arena e para
  ser conectada como MCP.
- Se a prioridade for **produto open-source com UI rica**, a melhor escolha é
  `affromero/flight-finder`.
- Se a prioridade for **agente que reserva**, a melhor escolha é `LetsFG`.
- Para **produção 24/7**, combine: TripWatch (ou flight-finder) + Docker + provedor real
  (SerpAPI/LetsFG) + webhook de notificação + HTTPS/autenticação.

## Fontes

- GitHub REST API (`api.github.com/repos/...`) — metadados, estrelas, licenças, datas.
- READMEs consultados via API (`Accept: application/vnd.github.raw`).
- [LetsFG](https://github.com/LetsFG/LetsFG) · [flight-finder](https://github.com/affromero/flight-finder) ·
  [travel-hacking-toolkit](https://github.com/borski/travel-hacking-toolkit) ·
  [flight-spy](https://github.com/jeancsil/flight-spy) · [swoop](https://github.com/saraswatayu/swoop) ·
  [trvl](https://github.com/MikkoParkkola/trvl) · [flightclaw](https://github.com/flightclaw/agents) ·
  [travel-agent-skills](https://github.com/mtnrabi/travel-agent-skills) ·
  [travel-agent](https://github.com/ruchirpipalia-spec/travel-agent)
