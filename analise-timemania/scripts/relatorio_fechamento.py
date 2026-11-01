#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera FECHAMENTO-TIMEMANIA.md a partir de dados/fechamento.json."""

import json
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(BASE, "dados", "fechamento.json"), encoding="utf-8"))
T = D["tabela"]
PRE = D["premissas"]


def n(x, dec=0):
    """Número no padrão brasileiro."""
    if dec:
        return f"{x:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"{int(round(x)):,}".replace(",", ".")


def pct(x, dec=1):
    return f"{x:.{dec}f}".replace(".", ",") + "%"


def brl(x):
    return "R$ " + n(x)


def linha_etapa(r, i):
    return (f"| {i}º | {r['v']} | {n(r['sem_filtro'])} | {n(r['com_filtro'])} | "
            f"{pct(r['reducao_pct'])} | {n(r['novas_sem_filtro'])} | {n(r['novas_com_filtro'])} | "
            f"{pct(100 * r['p_v_universo'], 3)} |")


total_sem = sum(r["sem_filtro"] for r in T)
total_com = sum(r["com_filtro"] for r in T)
total_min = sum(r["minimo_schoenheim"] for r in T)

tabela_etapas = "\n".join([
    "| Etapa | Dezenas (v) | Apostas únicas SEM filtro | Apostas únicas COM filtro | Redução | Novas sem filtro | Novas com filtro | Sorteio cair no universo |",
    "|---|---:|---:|---:|---:|---:|---:|---:|",
] + [linha_etapa(r, i) for i, r in enumerate(T, 1)])

tabela_custos = "\n".join([
    "| Dezenas (v) | Mínimo teórico (Schönheim) | Custo mínimo | Apostas com filtro | Custo com filtro | Múltiplo (filtro ÷ mínimo) |",
    "|---:|---:|---:|---:|---:|---:|",
] + [
    f"| {r['v']} | {n(r['minimo_schoenheim'])} | {brl(r['custo_minimo'])} | {n(r['com_filtro'])} | "
    f"{brl(r['custo_com_filtro'])} | {n(r['com_filtro'] / r['minimo_schoenheim'], 0)}× |"
    for r in T
])

tabela_base = "\n".join([
    "| Dezenas (v) | Apostas possíveis C(v,10) | Resultados possíveis C(v,7) | Apostas p/ cobrir (contagem) | Apostas p/ cobrir (Schönheim) | Custo do fechamento mínimo |",
    "|---:|---:|---:|---:|---:|---:|",
] + [
    f"| {r['v']} | {n(r['sem_filtro'])} | {n(math.comb(r['v'], 7))} | "
    f"{n(r['minimo_contagem'])} | {n(r['minimo_schoenheim'])} | {brl(r['custo_minimo'])} |"
    for r in T
])

funil = "\n".join([
    "| Filtro acumulado | Apostas restantes | % do total | Cortadas nesta etapa |",
    "|---|---:|---:|---:|",
] + [
    f"| {f['rotulo']} | {n(f['apostas'])} | {pct(100 * f['apostas'] / D['funil_20'][0]['apostas'])} | "
    f"{n((D['funil_20'][i - 1]['apostas'] if i else D['funil_20'][0]['apostas']) - f['apostas']) if i else '—'} |"
    for i, f in enumerate(D["funil_20"])
])

# mesmo orçamento: fechamento garantido do universo de 20 vs apostas aleatórias
r20 = T[0]
p_garantida = 100 * math.comb(20, 7) / math.comb(80, 7)
p_bruta_min = 100 * r20["minimo_schoenheim"] * 120 / math.comb(80, 7)
p_bruta_filtro = 100 * r20["com_filtro"] * 120 / math.comb(80, 7)
custo_acum = total_com * 3.5
razao_min80 = custo_acum / T[-1]["custo_minimo"]

doc = f"""# Fechamento matemático Timemania — 20 a 80 dezenas, organizados 10 a 10

**Objeto:** quantitativo de apostas únicas da matriz **v-10-7-7** (v dezenas escolhidas, apostas de 10, 7 sorteadas, garantia de 7 acertos) para v = 20, 30, 40, 50, 60, 70 e 80 — **sem filtro** e **com filtros**.
**Base:** 80 dezenas, 7 sorteadas, aposta fixa de 10 dezenas ({"R$ 3,50"}). O **Time do Coração foi ignorado** (sorteio independente, 1 em 80).
**Sorteio de referência (anterior):** concurso {PRE['sorteio_anterior']['concurso']} — {" ".join(f"{d:02d}" for d in PRE['sorteio_anterior']['dezenas'])}.
**Universo:** as v dezenas de maior frequência histórica (2.460 concursos) — em 20 dezenas: {" ".join(f"{d:02d}" for d in D['universo_dezenas'][:20])}.

---

## 0. Resultado direto

| Etapa | Dezenas | Matriz | Apostas SEM filtro | Apostas COM filtro | Redução |
|---|---:|---|---:|---:|---:|
{chr(10).join([
    f"| {i}º | {r['v']} | {r['v']}-10-7-7 | {n(r['sem_filtro'])} | {n(r['com_filtro'])} | {pct(r['reducao_pct'])} |"
    for i, r in enumerate(T, 1)
])}

**Em uma frase:** o fechamento de 20 dezenas tem {n(T[0]['sem_filtro'])} apostas possíveis e cai para {n(T[0]['com_filtro'])} com os filtros ({pct(T[0]['reducao_pct'])} de corte); no universo completo de 80 dezenas são {n(T[-1]['sem_filtro'])} → {n(T[-1]['com_filtro'])} ({pct(T[-1]['reducao_pct'])} de corte). A redução **não** é constante e **não** transforma o conjunto em fechamento: o piso real de um fechamento 80-10-7-7 é de apenas {n(T[-1]['minimo_schoenheim'])} apostas.

---

## 1. Regras que valem para todos os cálculos futuros

| Item | Regra fixa |
|---|---|
| Universo | 80 dezenas (01–80) |
| Dezenas sorteadas por concurso | 7 |
| Dezenas por aposta | 10 (não existe volante ampliado na Timemania) |
| Preço da aposta | R$ 3,50 |
| Prêmios | 7 acertos 1 em 26.472.637 · 6 em 216.103 · 5 em 5.220 · 4 em 276 · 3 em 29 |
| Time do Coração | **fora deste estudo** |
| Repetição do concurso anterior | **0 a 1 dezena = padrão** (88,7% no histórico) · **≥ 2 = zebra** (9,9%) |
| Paridade | 4P/3I (29,8%) e 3P/4I (27,7%) no centro · 2P/5I (16,3%) é zebra |
| Faixas de 10 dezenas | distribuição equilibrada (2.074 a 2.218 aparições no histórico) |

**Filtros aplicados às apostas de 10 dezenas** (tradução dos padrões das 7 sorteadas para o bilhete):

| Código | Filtro na aposta de 10 | Origem |
|---|---|---|
| F1 | no máximo **1** dezena do sorteio anterior | repetição 0–1 (88,7%) |
| F2 | **4 a 6** dezenas pares | paridade central; 2P/5I é zebra |
| F3 | **4 a 6** faixas de 10 ocupadas | equilíbrio entre faixas |
| F4 | maior bloco consecutivo **≤ 2** | cauda rara (bloco ≥ 3 = 3,1%) |

---

## 2. Quantitativo base (sem filtro) e o custo da garantia

| Dezenas (v) | Apostas possíveis C(v,10) | Resultados possíveis C(v,7) | Apostas p/ cobrir (contagem) | Apostas p/ cobrir (Schönheim) | Custo do fechamento mínimo |
|---:|---:|---:|---:|---:|---:|
{chr(10).join(tabela_base.splitlines()[2:])}

*"Apostas p/ cobrir" = mínimo teórico para garantir 7 acertos se o sorteio cair dentro das v dezenas. "Contagem" = C(v,7)/120 (cada aposta de 10 cobre 120 resultados de 7). "Schönheim" = limite inferior combinatório mais forte — é o piso real do fechamento.*

**Leitura:** o fechamento de 20 dezenas precisa de ~**{n(T[0]['minimo_schoenheim'])}** apostas ({brl(T[0]['custo_minimo'])}), e não de {n(T[0]['sem_filtro'])} — o universo de apostas é **{n(T[0]['sem_filtro'] / T[0]['minimo_schoenheim'])}×** maior que o necessário. No universo completo, o piso é **{n(T[-1]['minimo_schoenheim'])}** apostas ({brl(T[-1]['custo_minimo'])}).

---

## 3. Funil dos filtros no universo de 20 dezenas

{funil}

O primeiro filtro (repetição ≤ 1) é o mais forte, mas note que ele age sobre as **{len(set(D['universo_dezenas'][:20]) & set(PRE['sorteio_anterior']['dezenas']))} dezenas do sorteio anterior presentes no universo de 20** — se o universo contivesse as 7, o corte seria ainda maior.

---

## 4. Evolução passo a passo (resultado principal)

{tabela_etapas}

*Colunas "Novas": apostas que a etapa acrescenta em relação à etapa anterior (as anteriores continuam válidas, pois os universos são aninhados: as 20 primeiras dezenas estão contidas nas 30, e assim por diante).*

**Totais do ciclo completo (mantendo todas as apostas de todas as etapas):**

| | Sem filtro | Com filtro | Fechamento mínimo teórico |
|---|---:|---:|---:|
| Apostas únicas | {n(total_sem)} | {n(total_com)} | {n(total_min)} |
| Custo | {brl(total_sem * 3.5)} | {brl(total_com * 3.5)} | {brl(total_min * 3.5)} |

---

## 5. Diferença entre "sem filtro" e "com filtro"

| Dezenas (v) | Sem filtro | Com filtro | Apostas eliminadas | Redução | Custo evitado |
|---:|---:|---:|---:|---:|---:|
""" + "\n".join([
    f"| {r['v']} | {n(r['sem_filtro'])} | {n(r['com_filtro'])} | {n(r['sem_filtro'] - r['com_filtro'])} | "
    f"{pct(r['reducao_pct'])} | {brl((r['sem_filtro'] - r['com_filtro']) * 3.5)} |"
    for r in T
]) + f"""

**Conclusões numéricas:**

1. **A redução não é constante:** de {pct(min(r['reducao_pct'] for r in T))} (universo cheio) a {pct(max(r['reducao_pct'] for r in T))} (20 dezenas). É grande em 20 dezenas porque F2/F3/F4 cortam muito um universo pequeno, e cai para ~{pct(T[-1]['reducao_pct'])} no universo cheio, quando F1 (repetição ≤ 1) vira o filtro dominante e saturado.
2. **Cada nova camada de 10 dezenas custa caro:** sair de 20 para 30 multiplica as apostas por **{n(T[1]['com_filtro'] / T[0]['com_filtro'], 0)}×**; de 70 para 80, por **{n(T[6]['com_filtro'] / T[5]['com_filtro'], 0)}×**.
3. **O universo filtrado continua gigantesco:** no fechamento de 80 dezenas sobram {n(T[-1]['com_filtro'])} apostas — **{n(T[-1]['com_filtro'] / T[-1]['minimo_schoenheim'], 0)}×** o mínimo teórico e **{n(T[-1]['com_filtro'] / 3176716400, 0)}×** o número de resultados possíveis (3.176.716.400). Filtrar **não** é fechar.

---

## 6. Custo da garantia × custo do filtro

{tabela_custos}

O múltiplo cresce de **{n(T[0]['com_filtro'] / T[0]['minimo_schoenheim'], 0)}×** (20 dezenas) a **{n(T[-1]['com_filtro'] / T[-1]['minimo_schoenheim'], 0)}×** (80 dezenas): quanto maior o universo, mais longe o conjunto filtrado fica de um fechamento de verdade.

---

## 7. Leitura crítica (o que esses números decidem)

**7.1 Os filtros não melhoram a garantia — eles a reduzem.** Um fechamento v-10-7-7 garante 7 acertos **se** o sorteio cair dentro das v dezenas. Ao descartar apostas por filtro, você deixa de cobrir os resultados cuja única cobertura era uma aposta descartada: a garantia deixa de ser 100% e passa a depender de um cálculo de cobertura que **não** é dado pela contagem de apostas. Contagem com filtro responde "quantas apostas sobram", não "quantos resultados continuam cobertos".

**7.2 Fechamento e probabilidade bruta competem.** Com o orçamento do fechamento mínimo de 20 dezenas ({n(T[0]['minimo_schoenheim'])} apostas = {brl(T[0]['custo_minimo'])}):

| Estratégia | Chance de 7 acertos | Garantia |
|---|---|---|
| Fechamento garantido do universo de 20 (Schönheim ≈ {n(T[0]['minimo_schoenheim'])} apostas) | {pct(p_garantida, 5)}% | 100% se o sorteio cair nas 20 dezenas |
| {n(T[0]['minimo_schoenheim'])} apostas aleatórias distintas | até {pct(p_bruta_min, 5)}% | nenhuma |
| {n(T[0]['com_filtro'])} apostas filtradas (etapa 1) | até {pct(p_bruta_filtro, 4)}% | nenhuma |

Ou seja: **o fechamento compra garantia condicional, não probabilidade**. Para probabilidade bruta, espalhar apostas rende mais; para "não perder o sorteio se ele cair no meu grupo", o fechamento é insubstituível.

**7.3 O ciclo completo é financeiramente inviável.** Manter todas as apostas das 7 etapas custaria {brl(custo_acum)} com filtro ({brl(total_sem * 3.5)} sem filtro). Para dimensionar: são {n(razao_min80, 0)}× o custo do fechamento mínimo teórico do universo completo ({brl(T[-1]['custo_minimo'])}) e {n(custo_acum / 24000000, 0)}× o prêmio estimado do próximo concurso (R$ 24 milhões). O caminho matemático correto não é enumerar: é **projetar a cobertura**.

**7.4 O que a evolução de dezenas realmente entrega.** Acrescentar 10 dezenas por etapa aumenta a probabilidade de o sorteio estar dentro do universo (de {pct(100 * T[0]['p_v_universo'], 4)} em 20 dezenas para {pct(100 * T[2]['p_v_universo'], 2)} em 40, {pct(100 * T[3]['p_v_universo'], 2)} em 50 e {pct(100 * T[-1]['p_v_universo'], 1)} em 80), mas **não** aumenta a cobertura das apostas já registradas: elas continuam valendo apenas para as dezenas que já continham. Ganho real só existe se as novas apostas cobrirem as **novas** dezenas — e é exatamente isso que as colunas "Novas com filtro" medem.

---

## 8. Próximo passo recomendado (para a etapa seguinte do projeto)

| Passo | O que fazer | Por quê |
|---|---|---|
| 1 | Escolher a matriz a fechar: **20-10-7-7 com {n(T[0]['minimo_schoenheim'])} a {n(T[0]['minimo_schoenheim'] + 200)} apostas** ({brl(T[0]['custo_minimo'])} a {brl((T[0]['minimo_schoenheim'] + 200) * 3.5)}) | é o único fechamento do ciclo com custo praticável |
| 2 | Construir a cobertura com algoritmo de *covering design* (greedy + busca local), medindo a cobertura efetiva | contagem ≠ cobertura; é preciso provar que os C(20,7) resultados estão cobertos |
| 3 | Aplicar F1–F4 **depois** da cobertura, medindo quantos resultados ficaram descobertos | os filtros são critérios de escolha estética/probabilística, não de garantia |
| 4 | Se o objetivo for só filtro (sem garantia): ficar em **20 a 30 dezenas**; acima disso o volume de apostas deixa de ser jogável | ver coluna "Múltiplo" da seção 6 |

---

## 9. Reprodutibilidade

```bash
cd analise-timemania
python3 scripts/fechamento.py          # recalcula todos os quantitativos (dados/fechamento.json)
python3 scripts/relatorio_fechamento.py  # reescreve este documento
```

| Arquivo | Conteúdo |
|---|---|
| `filtros-timemania.json` | Premissas fixas: jogo, filtros 0–1/≥2, paridade, faixas, sorteio anterior |
| `dados/fechamento.json` | Quantitativos, mínimos teóricos, funil e custos |
| `scripts/fechamento.py` | Contagem exata por programação dinâmica + limites de Schönheim/contagem |

*Contagem "com filtro" = número exato de subconjuntos de 10 dezenas do universo que satisfazem F1–F4 (programação dinâmica sobre 80 posições, verificada contra C(v,10) quando os filtros são desligados e contra Monte Carlo).*
"""

destino = os.path.join(BASE, "FECHAMENTO-TIMEMANIA.md")
open(destino, "w", encoding="utf-8").write(doc)
print(f"OK — {destino} ({len(doc)} bytes)")
