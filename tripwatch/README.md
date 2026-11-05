# TripWatch AI

**Rastreamento de voos e hotéis com agentes de IA, buscas agendadas e servidor MCP.**
Zero dependências externas: Python 3.11+ (biblioteca padrão), SQLite e HTML/CSS/JS puro.

> Repositório dentro deste checkout: `tripwatch/`. É autocontido e não altera o projeto Go
> `github-mcp-server` que o hospeda.

---

## Por que este projeto

A pergunta central é: **qual a melhor forma de rastrear passagens e hotéis com IA, agentes e
pesquisas programadas?** A resposta prática é separar quatro responsabilidades:

| Camada | Responsabilidade | Neste projeto |
|---|---|---|
| **Coleta** | Obter preço atual de voos/hotéis | `providers.py` (SerpAPI real ou simulador) |
| **Memória** | Guardar histórico de preços | SQLite (`snapshots`) |
| **Orquestração** | Executar buscas em intervalos, gerar alertas | `engine.py` + agendador em thread |
| **Inteligência** | Interpretar tendência, recomendar, conversar | `agent.py` (regras + LLM opcional) |
| **Exposição** | Permitir que um agente externo use as ferramentas | Servidor MCP em `/mcp` |

Com isso, o mesmo backend serve para o painel web, para o agente de chat e para qualquer
cliente MCP (Arena, Claude Desktop, Cursor, VS Code).

---

## Começar em 30 segundos

O preview já está rodando. Para subir novamente:

```bash
cd tripwatch
python3 app.py
# → http://localhost:8787
```

Requisitos: apenas **Python 3.11+**. Não há `pip install`.

Variáveis úteis:

```bash
PORT=8787 python3 app.py
TRIPWATCH_DB=/data/tripwatch.db python3 app.py     # banco em outro volume
TRIPWATCH_PROVIDER=demo python3 app.py            # força o simulador
```

O banco de demonstração é criado automaticamente no primeiro start, com 5 watchlists,
30 dias de histórico e alertas de exemplo.

---

## O que está incluído

- **Painel web** com KPIs, radar de oportunidades, sparklines, histórico e alertas.
- **Watchlists de voos e hotéis** com preço-alvo, intervalo e pausa/retomada.
- **Agendador em segundo plano**: checa cada item no intervalo definido, sem intervention.
- **Alertas** de preço-alvo, queda e alta, com marcação de leitura.
- **Agente** que:
  - calcula tendência (média, mínimo, inclinação, volatilidade e confiança);
  - recomenda **Comprar agora / Aguardar / Observar**;
  - gera briefing do dia;
  - entende comandos em português e cria watchlists;
  - usa LLM opcional para linguagem natural.
- **Servidor MCP** com 12 ferramentas para o Arena/Claude/Cursor usarem o monitoramento.
- **Provedor real opcional** via SerpAPI (Google Flights + Google Hotels).
- **Dockerfile** e `run.sh` para deploy 24/7.

---

## Como funciona

```
                ┌──────────────────────────────┐
                │  Painel web /  Chat /  MCP   │
                └──────────────┬───────────────┘
                               │ HTTP + JSON-RPC
┌──────────────────────────────▼───────────────┐
│ app.py  (API REST + MCP + scheduler thread)  │
│                                              │
│  engine.run_check()  ──► providers.search()  │
│         │                    demo/SerpAPI    │
│         ▼                                    │
│  snapshots + alerts + runs  (SQLite)         │
│         │                                    │
│         ▼                                    │
│  agent.analyze()  ──►  briefing / chat       │
│         │                    regras + LLM    │
└─────────┴────────────────────────────────────┘
```

1. O usuário cria um watchlist (voo ou hotel) e define um preço-alvo.
2. O agendador executa `engine.run_check()` no intervalo configurado.
3. O provedor devolve o preço; o valor é gravado em `snapshots`.
4. Se o preço cruzar o alvo ou variar mais de 5%, um alerta é criado.
5. O agente lê o histórico e produz recomendação, confiança e reasons.
6. O painel e o MCP expõem tudo para o usuário e para outros agentes.

### Modelo de dados (SQLite)

- `watches` — o que monitorar (kind, rota/cidade, datas, alvo, intervalo).
- `snapshots` — série temporal de preços (`price`, `provider`, `found_at`).
- `alerts` — eventos de preço-alvo, queda e alta.
- `runs` — log de cada execução do agendador.
- `settings` — preferências globais.

---

## Provedores de preço

### 1. Demo (padrão, sem chave)

`DemoProvider` gera um preço determinístico por janela de 3 horas, com tendência, ruído e
promoções ocasionais. O objetivo é validar todo o fluxo (histórico, alertas, agente, MCP)
sem custo e sem chave. **Não é um preço de mercado.**

### 2. SerpAPI (dados reais)

```bash
export SERPAPI_KEY="sua_chave"
python3 app.py
```

- Voos: `engine=google_flights` (origem/destino IATA, datas, cabine).
- Hotéis: `engine=google_hotels` (cidade/hotel, check-in/check-out, hóspedes/quartos).
- Moeda e país configuráveis: `SERPAPI_CURRENCY`, `SERPAPI_HL`, `SERPAPI_GL`.
- Se a chamada falhar, o sistema **cai no simulador automaticamente** e registra o motivo no
  snapshot (`meta.error`), sem perder a execução.

> A SerpAPI é um serviço pago com cota gratuita. O TripWatch não faz scraping de sites de
> viagem: usa a API oficial do provedor. Respeite os termos dos provedores e a legislação
> local. Este projeto não realiza reservas nem pagamentos.

### 3. Outros MCPs de viagem

O TripWatch pode conviver com um MCP externo (por exemplo, LetsFG) no mesmo cliente. A
arquitetura de agentes permite que o agente externo consulte o TripWatch via `/mcp` e use
outro provedor para booking. Veja [`../docs/REPOSITORIOS.md`](../docs/REPOSITORIOS.md).

---

## Agendador e alertas

- Cada watchlist tem `interval_minutes` (padrão 180).
- O loop roda a cada 20 s e executa apenas os itens vencidos.
- `POST /api/check-all` força uma checagem imediata.
- Alertas:
  - **target**: preço `<=` alvo;
  - **drop**: queda `>= alert_drop_pct` (padrão 5%) entre coletas;
  - **rise**: alta `>= 8%`.
- Alertas duplicados do mesmo tipo são evitados por 8 horas.
- O agendador só roda enquanto o processo está vivo. Para 24/7, use Docker, Railway, Fly.io
  ou um serviço equivalente.

---

## Agente IA

### Análise local (sempre disponível)

Para cada watchlist, o agente calcula:

- posição do preço atual vs. média de 30 dias;
- mínimo/máximo histórico e quando ocorreram;
- variação de 7 dias e inclinação (regressão linear);
- volatilidade e confiança;
- distância até o preço-alvo.

A recomendação sai em três faixas:

| Sinal | Regra resumida | Label |
|---|---|---|
| Compra | preço <= alvo*1.01 **ou** preço <= mínimo*1.025 e <= média*0.975 | **Comprar agora** |
| Espera | alta de 7 dias > 3,5% **ou** inclinação positiva acima da média | **Aguardar** |
| Observa | demais casos | **Observar** |

### LLM opcional (briefing e conversa)

Configure uma chave para respostas em linguagem natural:

```bash
export OPENAI_API_KEY="sk-..."          # OpenAI
# ou
export ANTHROPIC_API_KEY="sk-ant-..."   # Anthropic
# ou um endpoint compatível com OpenAI
export LLM_BASE_URL="https://..." LLM_API_KEY="..." LLM_MODEL="..."
```

O LLM **não substitui** os cálculos: ele recebe o contexto estruturado e escreve o briefing.
Se a chamada falhar, a análise local continua funcionando.

### Comandos que o agente entende

- `Monitore THE → LIS em 15/12, abaixo de R$ 4.300`
- `Monitore hotel em Lisboa de 10/01 a 14/01 até R$ 700`
- `Quanto está Teresina → Lisboa?`
- `Rodar checagem agora`
- `Me mostre os alertas`
- `Faça um briefing das oportunidades`

---

## Conectar no Arena (MCP)

O TripWatch expõe um servidor **MCP Streamable HTTP (JSON-RPC 2.0)** em `/mcp`.

1. Abra o preview do TripWatch (ou rode `python3 app.py`).
2. Copie a URL: `https://<host-do-preview>/mcp`.
3. No Arena/Claude/Cursor, adicione um servidor MCP remoto com essa URL.
4. Peça ao agente: *"liste os watchlists do TripWatch e faça um briefing"*.

Configuração equivalente (Claude Desktop / Cursor):

```json
{
  "mcpServers": {
    "tripwatch": {
      "type": "http",
      "url": "https://<host-do-preview>/mcp"
    }
  }
}
```

Para clientes stdio, use um bridge:

```bash
npx mcp-remote https://<host-do-preview>/mcp
```

### Ferramentas expostas

| Ferramenta | O que faz |
|---|---|
| `search_flights` | busca preço de voo (sem persistir) |
| `search_hotels` | busca preço de hotel (sem persistir) |
| `track_flight` | cria watchlist de voo e já coleta o primeiro preço |
| `track_hotel` | cria watchlist de hotel e já coleta o primeiro preço |
| `list_watchlist` | lista itens com análise do agente |
| `get_price_history` | histórico completo de um item |
| `run_check` | checa um item ou todos |
| `travel_briefing` | briefing do dia (com `use_llm: true` opcional) |
| `list_alerts` | alertas recentes |
| `update_target` | atualiza o preço-alvo |
| `delete_watch` | remove um monitoramento |
| `agent_chat` | conversa com ferramentas em linguagem natural |

Teste rápido:

```bash
curl -s -X POST http://localhost:8787/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

curl -s -X POST http://localhost:8787/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"travel_briefing","arguments":{}}}'
```

> A URL `/mcp` é a mesma do painel. Em produção, coloque atrás de HTTPS e de um proxy com
> autenticação. O preview do Arena já fornece HTTPS.

---

## API REST

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/state` | watchlists + análise + alertas + settings + briefing |
| POST | `/api/watches` | cria watchlist e coleta o primeiro preço |
| PATCH | `/api/watches/:id` | atualiza alvo, intervalo, pausa, datas |
| DELETE | `/api/watches/:id` | remove watchlist, histórico e alertas |
| POST | `/api/watches/:id/check` | checagem imediata |
| POST | `/api/check-all` | checa todos os itens vencidos/forçados |
| GET | `/api/briefing` | briefing local |
| POST | `/api/briefing` | briefing com LLM (`{"use_llm": true}`) |
| POST | `/api/agent/chat` | chat do agente |
| GET | `/api/agent/context` | contexto completo para um agente externo |
| POST | `/api/alerts/read` | marca alerta(s) como lido(s) |
| POST | `/api/settings` | atualiza preferências |
| POST | `/api/reset-demo` | restaura o banco de demonstração |
| GET | `/api/health` | healthcheck |
| POST | `/mcp` | MCP JSON-RPC |

Exemplo:

```bash
curl -s -X POST http://localhost:8787/api/watches \
  -H 'Content-Type: application/json' \
  -d '{"kind":"flight","origin":"THE","destination":"LIS","depart_date":"2026-12-15","return_date":"2026-12-22","target_price":4300}'
```

---

## Docker (24/7)

```bash
cd tripwatch
docker build -t tripwatch-ai .
docker run -d --name tripwatch -p 8787:8787 \
  -e SERPAPI_KEY=sua_chave \
  -v tripwatch-data:/data \
  tripwatch-ai
```

O banco fica em `/data/tripwatch.db` (defina `TRIPWATCH_DB=/data/tripwatch.db`).

---

## Comparação rápida com repositórios existentes

| Repositório | Estrelas | Stack | Licença | Melhor para |
|---|---:|---|---|---|
| **LetsFG/LetsFG** | ~2.230 | Python, MCP, SDKs | outra (ver repo) | busca e **booking** real de voos/hotéis via agente |
| **affromero/flight-finder** | ~183 | TypeScript, Next.js, Prisma | MIT | self-hosted completo com Playwright, Postgres, cron e charts |
| **borski/travel-hacking-toolkit** | ~888 | Python, skills/MCP | MIT | milhas, pontos e award flights |
| **jeancsil/flight-spy** | ~185 | PHP | MIT | alertas de preço via Skyscanner |
| **saraswatayu/swoop** | ~101 | Python | MIT | Google Flights sem API key |
| **MikkoParkkola/trvl** | ~93 | Go, binário único | PolyForm NC | MCP local sem API keys (não comercial) |
| **flightclaw/agents** | ~82 | Python, MCP | MIT | tracking diário + email e booking |
| **mtnrabi/travel-agent-skills** | ~4 | skills | MIT | 8 skills de preço para Claude Code/OpenClaw |
| **ruchirpipalia-spec/travel-agent** | 0 | Python, Telegram | sem licença | referência de agente com SerpAPI + Claude |

Análise completa, com veredito e quando usar cada um: [`../docs/REPOSITORIOS.md`](../docs/REPOSITORIOS.md).

### Recomendação

- **Quer rodar agora no Arena, sem chave e sem instalar nada?** Use o **TripWatch AI** (este
  diretório). Ele já está de pé, tem MCP e agenda checagens.
- **Quer a melhor base open-source de mercado, com UI completa e scraping?** Use
  **affromero/flight-finder** como referência de produto; o TripWatch é a versão enxuta e
  autocontida.
- **Quer preços reais e booking?** Conecte o **LetsFG** (MCP) ou configure a **SerpAPI** no
  TripWatch. Para milhas/pontos, use o **travel-hacking-toolkit**.
- **Quer um MCP local sem chaves?** **trvl** (licença não comercial).

---

## Limitações conhecidas

- O modo demo **não usa preços reais**; é um validador de fluxo.
- O agendador é em-processo: se o processo morrer, as checagens param. Use Docker/serviço
  gerenciado para produção.
- Não há autenticação no painel. Em exposição pública, coloque atrás de um proxy com login.
- O webhook de alertas é configurável, mas o envio ainda não está implementado nesta versão
  (o campo fica reservado). Alertas ficam no painel e na API.
- O TripWatch não reserva nem paga passagens/hotéis; ele mede e recomenda. O booking, se
  desejado, deve ser feito por um provedor homologado.

## Próximos passos

- Webhook real (Telegram/Slack/e-mail) e notificação push.
- Comparador de datas flexíveis (±3 dias) e de hotéis alternativos.
- Booking link/afiliado e deep link para o provedor.
- Autenticação e multiusuário.
- Export CSV/JSON do histórico.

## Licença

O código deste diretório segue a licença MIT do repositório que o hospeda
(`github/github-mcp-server`). Consulte `../LICENSE`.
