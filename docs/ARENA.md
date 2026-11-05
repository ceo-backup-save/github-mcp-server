# Instalar o TripWatch AI no Arena

O Arena (Agent Mode) roda este projeto em um sandbox com **preview ao vivo**. A aplicação
já foi projetada para esse ambiente:

- escuta em `0.0.0.0` (não em `127.0.0.1`);
- aceita requisições do host de preview (sem allowlist de domínio);
- usa URLs relativas no frontend (sem chamar `localhost` do navegador);
- não exige `npm install`, compilação ou banco externo.

## Opção A — usar o que já está rodando (recomendado)

1. Abra o preview do **TripWatch AI** (porta 8787).
2. O painel já vem com 5 watchlists de demonstração, 30 dias de histórico e alertas.
3. Copie a URL do preview e use `/mcp` como servidor MCP:

   ```
   https://<id-do-sandbox>-8787.e2b.app/mcp
   ```

4. No Arena/Claude/Cursor, adicione um servidor MCP remoto com essa URL.
5. Teste no chat do agente:

   > Liste os watchlists do TripWatch e faça um briefing das oportunidades.

O preview é ideal para validar o fluxo. **Ele não é 24/7**: se o processo do sandbox for
encerrado, o agendador para. Para produção, use a Opção C.

## Opção B — conectar o MCP do TripWatch

O endpoint `/mcp` fala **MCP Streamable HTTP com JSON-RPC 2.0**. Handshake:

```bash
curl -s -X POST http://localhost:8787/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

Resposta esperada:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": { "tools": { "listChanged": false } },
    "serverInfo": { "name": "tripwatch-ai", "version": "1.0.0" }
  }
}
```

Configuração de cliente (Claude Desktop, Cursor, VS Code):

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

Clientes que só aceitam stdio:

```bash
npx mcp-remote https://<host-do-preview>/mcp
```

> Em produção, coloque o `/mcp` atrás de HTTPS e autenticação. O painel e o MCP não têm
> login próprio nesta versão.

## Catálogo de repositórios

A aba **Repositórios** do painel já inclui o **LetsFG/LetsFG** (`https://letsfg.co/mcp`,
`pip install letsfg`) e mais 9 ferramentas. O catálogo é servido por:

- `GET /api/repos` — lista;
- `POST /api/repos` — adiciona/atualiza;
- MCP `list_repos` e `add_repo`;
- arquivo exportado `docs/catalogo-repositorios.json`.

Para o agente usar o LetsFG como provedor de preço/booking, conecte
`https://letsfg.co/mcp` como MCP no Arena/Claude/Cursor. O TripWatch continua como memória,
agendador e alertas.

## Opção C — rodar 24/7 (Docker)

```bash
cd tripwatch
docker build -t tripwatch-ai .
docker run -d --name tripwatch -p 8787:8787 \
  -e SERPAPI_KEY=sua_chave \
  -e OPENAI_API_KEY=sk-... \
  -v tripwatch-data:/data \
  -e TRIPWATCH_DB=/data/tripwatch.db \
  tripwatch-ai
```

Acesse `http://localhost:8787` e o MCP em `http://localhost:8787/mcp`.

Alternativas: Railway, Fly.io, Render, VPS com Docker Compose + Caddy (HTTPS automático).

## Variáveis de ambiente

| Variável | Padrão | Efeito |
|---|---|---|
| `PORT` | `8787` | porta HTTP |
| `TRIPWATCH_HOST` | `0.0.0.0` | interface de bind |
| `TRIPWATCH_DB` | `tripwatch/data/tripwatch.db` | caminho do SQLite |
| `TRIPWATCH_PROVIDER` | `auto` | `auto`, `demo` ou `serpapi` |
| `TRIPWATCH_DISABLE_SCHEDULER` | — | desliga o agendador (testes) |
| `SERPAPI_KEY` | — | ativa Google Flights/Hotels reais |
| `SERPAPI_CURRENCY` | `BRL` | moeda das buscas |
| `SERPAPI_HL` | `pt-br` | idioma |
| `SERPAPI_GL` | `br` | país |
| `OPENAI_API_KEY` | — | briefing/chat com OpenAI |
| `ANTHROPIC_API_KEY` | — | briefing/chat com Anthropic |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | endpoint compatível com OpenAI |
| `LLM_API_KEY` | — | chave do endpoint compatível |
| `LLM_MODEL` | `gpt-4o-mini` / `claude-3-5-sonnet-latest` | modelo |

Arquivo de referência: `.env.example`.

## Persistência

- O banco SQLite fica em `tripwatch/data/tripwatch.db` (WAL).
- No preview, os arquivos do workspace persistem entre turnos, mas o **processo** pode ser
  reiniciado. O histórico não se perde; o agendador volta a rodar no start.
- Para produção, monte um volume (`-v tripwatch-data:/data`) e faça backup do `.db`.

## Checklist de produção

- [ ] HTTPS no proxy reverso (Caddy/nginx/Traefik).
- [ ] Autenticação no painel e no `/mcp` (Basic Auth, OAuth do proxy, token).
- [ ] `SERPAPI_KEY` configurada e cota monitorada.
- [ ] Volume persistente para o SQLite + backup diário.
- [ ] Webhook de alertas (Telegram/Slack/e-mail) — campo reservado em `settings`.
- [ ] Healthcheck `GET /api/health` no orquestrador.
- [ ] Log de execuções (`runs`) e retenção.
- [ ] Revisão dos termos do provedor de preços e da legislação (LGPD).

## Verificação rápida

```bash
curl -s http://localhost:8787/api/health
curl -s http://localhost:8787/api/state | jq '.stats, .provider'
curl -s -X POST http://localhost:8787/api/check-all | jq
curl -s -X POST http://localhost:8787/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq '.result.tools[].name'
```

## Solução de problemas

| Sintoma | Causa provável | Correção |
|---|---|---|
| `Address already in use` | porta 8787 ocupada | `PORT=8788 python3 app.py` |
| Preview não abre | processo parado | rode `python3 app.py` novamente |
| Preços sempre iguais | modo demo | configure `SERPAPI_KEY` e reinicie |
| `SerpAPI HTTP 401` | chave inválita/sem cota | confira a chave e o plano |
| `Falha ao chamar o LLM` | chave/modelo inválido | o app cai na análise local; ajuste o modelo |
| Agendador parado | processo encerrado | use Docker/serviço 24/7 |
| MCP não conecta | URL sem `/mcp` ou host bloqueado | use a URL completa do preview e HTTPS |
| `404` em `/static/...` | caminho relativo | o app serve `/static` a partir de `tripwatch/static` |

## Limitações do ambiente de preview

- O preview pode ser reiniciado pelo provedor; não é garantia de 24/7.
- Não há autenticação: qualquer pessoa com a URL do preview pode ver os dados.
- O simulador é determinístico e não representa o mercado.
- Cota da SerpAPI e do provedor de LLM são de responsabilidade do usuário.
