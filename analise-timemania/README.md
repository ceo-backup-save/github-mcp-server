# Levantamento Timemania — últimos 100 concursos

Análise estatística descritiva da Timemania (Caixa Econômica Federal) sobre os
**100 concursos mais recentes** (2.362 a 2.461, de 03/03/2026 a 29/10/2026),
com validação contra o **histórico completo** (2.460 concursos, 2008–2026).

O documento principal é **[`LEVANTAMENTO-TIMEMANIA.md`](LEVANTAMENTO-TIMEMANIA.md)**:
tabelas de prevalência ≥ 70%, tabela de zebras (< 30%), repetição de dezenas,
testes de aderência ao sorteio uniforme, frequência e atraso das dezenas,
Time do Coração e os 100 sorteios listados um a um.

## Resultado em uma linha

Na Timemania o padrão mais sólido é a **repetição de 0 a 1 dezena do concurso
anterior** (90,0% no recorte, 88,7% no histórico) — que é exatamente o que o
sorteio uniforme já prevê (88,8%). Os testes de aderência (χ²) não rejeitam a
hipótese de sorteio justo em nenhuma das variáveis analisadas.

## Dados

`dados/timemania_bruto_espelho_caixa.json` é o espelho dos resultados oficiais
da API de loterias da Caixa
(`https://servicebus2.caixa.gov.br/portaldeloterias/api/timemania/{concurso}`),
mantido atualizado diariamente em `github.com/eitchtee/loterias.json`. O arquivo
segue o esquema da própria API:

```json
{"concurso": 2461, "data": "29/10/2026",
 "resultado": ["02", "06", "17", "39", "57", "64", "71"],
 "time_do_coracao": "INTER LIMEIRA /SP"}
```

Validações já executadas:

* conferência de 2.168 concursos contra base independente
  (`github.com/guilhermeasn/loteria.json`) — única divergência é o concurso 1307,
  que aparece com 8 dezenas no espelho e é descartado;
* conferência do concurso 2.461 contra quatro publicações independentes
  (dezenas e Time do Coração idênticos).

Para usar a API oficial diretamente (rede com acesso à Caixa), basta substituir
esse arquivo por uma coleta `GET .../api/timemania/{n}` no mesmo esquema.

## Como reproduzir

Somente biblioteca padrão do Python 3 (sem dependências):

```bash
cd analise-timemania
python3 scripts/analise_timemania.py   # métricas + tabelas (dados/metricas.json, dados/tabelas.md, CSV)
python3 scripts/gerar_relatorio.py     # reescreve LEVANTAMENTO-TIMEMANIA.md
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `LEVANTAMENTO-TIMEMANIA.md` | Relatório completo (documento principal). |
| `scripts/analise_timemania.py` | Carga, validação, 17 variáveis, IC de Wilson, χ² agrupado, hipergeométrico, validação cruzada. |
| `scripts/gerar_relatorio.py` | Monta o relatório a partir das métricas — texto e tabelas nunca divergem. |
| `dados/timemania_bruto_espelho_caixa.json` | Resultados oficiais espelhados (2.461 concursos). |
| `dados/timemania_ultimos_100.csv` | Os 100 concursos do recorte com soma, pares, primos, repetidas e time (`;`). |
| `dados/metricas.json` | Todas as métricas, distribuições e p-valores. |
| `dados/tabelas.md` | As tabelas em markdown. |

## Aviso

Os percentuais são **descritivos do histórico**. Em um sorteio justo nenhuma
combinação tem probabilidade maior que outra e nenhum filtro aumenta a chance de
prêmio: 7 acertos pagam 1 em 26.472.637 (aposta de 10 dezenas) e o Time do
Coração, 1 em 80.
