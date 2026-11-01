# Fechamento matemático Timemania — 20 a 80 dezenas, organizados 10 a 10

**Objeto:** quantitativo de apostas únicas da matriz **v-10-7-7** (v dezenas escolhidas, apostas de 10, 7 sorteadas, garantia de 7 acertos) para v = 20, 30, 40, 50, 60, 70 e 80 — **sem filtro** e **com filtros**.
**Base:** 80 dezenas, 7 sorteadas, aposta fixa de 10 dezenas (R$ 3,50). O **Time do Coração foi ignorado** (sorteio independente, 1 em 80).
**Sorteio de referência (anterior):** concurso 2461 — 02 06 17 39 57 64 71.
**Universo:** as v dezenas de maior frequência histórica (2.460 concursos) — em 20 dezenas: 21 20 61 70 80 72 66 12 35 71 04 65 39 50 06 11 41 44 57 60.

---

## 0. Resultado direto

| Etapa | Dezenas | Matriz | Apostas SEM filtro | Apostas COM filtro | Redução |
|---|---:|---|---:|---:|---:|
| 1º | 20 | 20-10-7-7 | 184.756 | 19.868 | 89,2% |
| 2º | 30 | 30-10-7-7 | 30.045.015 | 7.255.940 | 75,8% |
| 3º | 40 | 40-10-7-7 | 847.660.528 | 259.285.604 | 69,4% |
| 4º | 50 | 50-10-7-7 | 10.272.278.170 | 3.050.496.332 | 70,3% |
| 5º | 60 | 60-10-7-7 | 75.394.027.566 | 25.257.289.867 | 66,5% |
| 6º | 70 | 70-10-7-7 | 396.704.524.216 | 123.810.328.042 | 68,8% |
| 7º | 80 | 80-10-7-7 | 1.646.492.110.120 | 535.964.339.184 | 67,4% |

**Em uma frase:** o fechamento de 20 dezenas tem 184.756 apostas possíveis e cai para 19.868 com os filtros (89,2% de corte); no universo completo de 80 dezenas são 1.646.492.110.120 → 535.964.339.184 (67,4% de corte). A redução **não** é constante e **não** transforma o conjunto em fechamento: o piso real de um fechamento 80-10-7-7 é de apenas 27.188.152 apostas.

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
| 20 | 184.756 | 77.520 | 646 | 744 | R$ 2.604 |
| 30 | 30.045.015 | 2.035.800 | 16.965 | 16.986 | R$ 59.451 |
| 40 | 847.660.528 | 18.643.560 | 155.363 | 164.512 | R$ 575.792 |
| 50 | 10.272.278.170 | 99.884.400 | 832.370 | 832.510 | R$ 2.913.785 |
| 60 | 75.394.027.566 | 386.206.920 | 3.218.391 | 3.339.324 | R$ 11.687.634 |
| 70 | 396.704.524.216 | 1.198.774.720 | 9.989.790 | 9.990.050 | R$ 34.965.175 |
| 80 | 1.646.492.110.120 | 3.176.716.400 | 26.472.637 | 27.188.152 | R$ 95.158.532 |

*"Apostas p/ cobrir" = mínimo teórico para garantir 7 acertos se o sorteio cair dentro das v dezenas. "Contagem" = C(v,7)/120 (cada aposta de 10 cobre 120 resultados de 7). "Schönheim" = limite inferior combinatório mais forte — é o piso real do fechamento.*

**Leitura:** o fechamento de 20 dezenas precisa de ~**744** apostas (R$ 2.604), e não de 184.756 — o universo de apostas é **248×** maior que o necessário. No universo completo, o piso é **27.188.152** apostas (R$ 95.158.532).

---

## 3. Funil dos filtros no universo de 20 dezenas

| Filtro acumulado | Apostas restantes | % do total | Cortadas nesta etapa |
|---|---:|---:|---:|
| sem filtro | 184.756 | 100,0% | — |
| F1 repetição ≤ 1 | 53.768 | 29,1% | 130.988 |
| F1 + F2 pares 4–6 | 37.752 | 20,4% | 16.016 |
| F1 + F2 + F3 faixas 4–6 | 21.780 | 11,8% | 15.972 |
| F1 + F2 + F3 + F4 bloco ≤ 2 | 19.868 | 10,8% | 1.912 |

O primeiro filtro (repetição ≤ 1) é o mais forte, mas note que ele age sobre as **4 dezenas do sorteio anterior presentes no universo de 20** — se o universo contivesse as 7, o corte seria ainda maior.

---

## 4. Evolução passo a passo (resultado principal)

| Etapa | Dezenas (v) | Apostas únicas SEM filtro | Apostas únicas COM filtro | Redução | Novas sem filtro | Novas com filtro | Sorteio cair no universo |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1º | 20 | 184.756 | 19.868 | 89,2% | 184.756 | 19.868 | 0,002% |
| 2º | 30 | 30.045.015 | 7.255.940 | 75,8% | 29.860.259 | 7.236.072 | 0,064% |
| 3º | 40 | 847.660.528 | 259.285.604 | 69,4% | 817.615.513 | 252.029.664 | 0,587% |
| 4º | 50 | 10.272.278.170 | 3.050.496.332 | 70,3% | 9.424.617.642 | 2.791.210.728 | 3,144% |
| 5º | 60 | 75.394.027.566 | 25.257.289.867 | 66,5% | 65.121.749.396 | 22.206.793.535 | 12,157% |
| 6º | 70 | 396.704.524.216 | 123.810.328.042 | 68,8% | 321.310.496.650 | 98.553.038.175 | 37,736% |
| 7º | 80 | 1.646.492.110.120 | 535.964.339.184 | 67,4% | 1.249.787.585.904 | 412.154.011.142 | 100,000% |

*Colunas "Novas": apostas que a etapa acrescenta em relação à etapa anterior (as anteriores continuam válidas, pois os universos são aninhados: as 20 primeiras dezenas estão contidas nas 30, e assim por diante).*

**Totais do ciclo completo (mantendo todas as apostas de todas as etapas):**

| | Sem filtro | Com filtro | Fechamento mínimo teórico |
|---|---:|---:|---:|
| Apostas únicas | 2.129.740.830.371 | 688.349.014.837 | 41.532.278 |
| Custo | R$ 7.454.092.906.298 | R$ 2.409.221.551.930 | R$ 145.362.973 |

---

## 5. Diferença entre "sem filtro" e "com filtro"

| Dezenas (v) | Sem filtro | Com filtro | Apostas eliminadas | Redução | Custo evitado |
|---:|---:|---:|---:|---:|---:|
| 20 | 184.756 | 19.868 | 164.888 | 89,2% | R$ 577.108 |
| 30 | 30.045.015 | 7.255.940 | 22.789.075 | 75,8% | R$ 79.761.762 |
| 40 | 847.660.528 | 259.285.604 | 588.374.924 | 69,4% | R$ 2.059.312.234 |
| 50 | 10.272.278.170 | 3.050.496.332 | 7.221.781.838 | 70,3% | R$ 25.276.236.433 |
| 60 | 75.394.027.566 | 25.257.289.867 | 50.136.737.699 | 66,5% | R$ 175.478.581.946 |
| 70 | 396.704.524.216 | 123.810.328.042 | 272.894.196.174 | 68,8% | R$ 955.129.686.609 |
| 80 | 1.646.492.110.120 | 535.964.339.184 | 1.110.527.770.936 | 67,4% | R$ 3.886.847.198.276 |

**Conclusões numéricas:**

1. **A redução não é constante:** de 66,5% (universo cheio) a 89,2% (20 dezenas). É grande em 20 dezenas porque F2/F3/F4 cortam muito um universo pequeno, e cai para ~67,4% no universo cheio, quando F1 (repetição ≤ 1) vira o filtro dominante e saturado.
2. **Cada nova camada de 10 dezenas custa caro:** sair de 20 para 30 multiplica as apostas por **365×**; de 70 para 80, por **4×**.
3. **O universo filtrado continua gigantesco:** no fechamento de 80 dezenas sobram 535.964.339.184 apostas — **19.713×** o mínimo teórico e **169×** o número de resultados possíveis (3.176.716.400). Filtrar **não** é fechar.

---

## 6. Custo da garantia × custo do filtro

| Dezenas (v) | Mínimo teórico (Schönheim) | Custo mínimo | Apostas com filtro | Custo com filtro | Múltiplo (filtro ÷ mínimo) |
|---:|---:|---:|---:|---:|---:|
| 20 | 744 | R$ 2.604 | 19.868 | R$ 69.538 | 27× |
| 30 | 16.986 | R$ 59.451 | 7.255.940 | R$ 25.395.790 | 427× |
| 40 | 164.512 | R$ 575.792 | 259.285.604 | R$ 907.499.614 | 1.576× |
| 50 | 832.510 | R$ 2.913.785 | 3.050.496.332 | R$ 10.676.737.162 | 3.664× |
| 60 | 3.339.324 | R$ 11.687.634 | 25.257.289.867 | R$ 88.400.514.534 | 7.564× |
| 70 | 9.990.050 | R$ 34.965.175 | 123.810.328.042 | R$ 433.336.148.147 | 12.393× |
| 80 | 27.188.152 | R$ 95.158.532 | 535.964.339.184 | R$ 1.875.875.187.144 | 19.713× |

O múltiplo cresce de **27×** (20 dezenas) a **19.713×** (80 dezenas): quanto maior o universo, mais longe o conjunto filtrado fica de um fechamento de verdade.

---

## 7. Leitura crítica (o que esses números decidem)

**7.1 Os filtros não melhoram a garantia — eles a reduzem.** Um fechamento v-10-7-7 garante 7 acertos **se** o sorteio cair dentro das v dezenas. Ao descartar apostas por filtro, você deixa de cobrir os resultados cuja única cobertura era uma aposta descartada: a garantia deixa de ser 100% e passa a depender de um cálculo de cobertura que **não** é dado pela contagem de apostas. Contagem com filtro responde "quantas apostas sobram", não "quantos resultados continuam cobertos".

**7.2 Fechamento e probabilidade bruta competem.** Com o orçamento do fechamento mínimo de 20 dezenas (744 apostas = R$ 2.604):

| Estratégia | Chance de 7 acertos | Garantia |
|---|---|---|
| Fechamento garantido do universo de 20 (Schönheim ≈ 744 apostas) | 0,00244%% | 100% se o sorteio cair nas 20 dezenas |
| 744 apostas aleatórias distintas | até 0,00281%% | nenhuma |
| 19.868 apostas filtradas (etapa 1) | até 0,0751%% | nenhuma |

Ou seja: **o fechamento compra garantia condicional, não probabilidade**. Para probabilidade bruta, espalhar apostas rende mais; para "não perder o sorteio se ele cair no meu grupo", o fechamento é insubstituível.

**7.3 O ciclo completo é financeiramente inviável.** Manter todas as apostas das 7 etapas custaria R$ 2.409.221.551.930 com filtro (R$ 7.454.092.906.298 sem filtro). Para dimensionar: são 25.318× o custo do fechamento mínimo teórico do universo completo (R$ 95.158.532) e 100.384× o prêmio estimado do próximo concurso (R$ 24 milhões). O caminho matemático correto não é enumerar: é **projetar a cobertura**.

**7.4 O que a evolução de dezenas realmente entrega.** Acrescentar 10 dezenas por etapa aumenta a probabilidade de o sorteio estar dentro do universo (de 0,0024% em 20 dezenas para 0,59% em 40, 3,14% em 50 e 100,0% em 80), mas **não** aumenta a cobertura das apostas já registradas: elas continuam valendo apenas para as dezenas que já continham. Ganho real só existe se as novas apostas cobrirem as **novas** dezenas — e é exatamente isso que as colunas "Novas com filtro" medem.

---

## 8. Próximo passo recomendado (para a etapa seguinte do projeto)

| Passo | O que fazer | Por quê |
|---|---|---|
| 1 | Escolher a matriz a fechar: **20-10-7-7 com 744 a 944 apostas** (R$ 2.604 a R$ 3.304) | é o único fechamento do ciclo com custo praticável |
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
