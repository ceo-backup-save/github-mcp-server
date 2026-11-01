# Levantamento Timemania — últimos 100 concursos

**Recorte:** concursos **2362 a 2461** (03/03/2026 a 29/10/2026) — 100 sorteios
**Histórico de referência:** 2460 concursos (2008 a 29/10/2026)
**Fonte:** API oficial de loterias da Caixa (`servicebus2.caixa.gov.br/portaldeloterias/api/timemania`), lida por espelho diário e conferida contra base independente
**Gerado em:** 2026-11-01 04:07 · cada sorteio: 7 dezenas entre 80 + 1 Time do Coração entre 80 clubes

> **Nota metodológica.** Os percentuais abaixo são **descritivos do histórico**. Em um sorteio justo, nenhuma combinação tem probabilidade maior que outra, e nenhum filtro aumenta a chance de prêmio. A Timemania paga 1 em 26.472.637 para 7 acertos (aposta mínima de 10 dezenas) e 1 em 80 para o Time do Coração.

---

## Resumo executivo

**O que este levantamento traz de novo em relação ao anexo:** o anexo dizia que a Timemania "carece de uma tabela de filtros > 70% / < 30%". Com os 100 concursos mais recentes **e** com o histórico completo, é possível montar essa tabela: 17 variáveis foram calculadas no recorte, e todas têm um intervalo que cobre ≥ 70% dos sorteios — o que muda de uma para outra é a **largura** desse intervalo.

1. **Repetição do concurso anterior é o padrão mais robusto e foi confirmado.** 0 a 1 repetida cobre **90,0%** dos 100 sorteios e **88,7%** de todo o histórico — praticamente igual ao esperado por puro azar (**88,80%**). O valor de 88,7% citado no anexo está correto.
2. **Padrões estruturais com cobertura muito alta no recorte:** maior bloco consecutivo 1–2 (99,0%), quadrantes 3–4 (92,0%), pares adjacentes 0–1 (93,0%), concentração por faixa de 10 de 2–3 dezenas (93,0%).
3. **Padrões de composição:** pares 3–5 (82,0%), primos 1–3 (79,0%), Fibonacci 0–1 (85,0%), múltiplos de 3 1–3 (83,0%), terminações distintas 5–6 (78,0%).
4. **Zebras (caudas raras):** maior bloco ≥ 3 (1,0%), pares adjacentes = 2 (7,0%), 2 repetidas (10,0%), nenhum primo (21,0%), apenas 2 quadrantes ocupados (8,0%).
5. **Testes de aderência ao sorteio uniforme não rejeitam nada.** Soma, paridade, baixas, primos, múltiplos de 3, Fibonacci, moldura e a frequência das 80 dezenas: todos com p-valor acima de 0,05, no recorte e no histórico. Isto é, as "faixas de 70%" **descrevem** como os sorteios se distribuem — não revelam tendência.
6. **As faixas de 10 dezenas são levemente desiguais apenas por acaso** no recorte (de 72 a 99 aparições por faixa, contra 87,5 esperadas), e praticamente niveladas no histórico.

---

## 1. Base de dados, fonte e validação

| Item | Resultado |
|---|---|
| Registros lidos do espelho da API da Caixa | 2461 concursos (todos os existentes) |
| Concursos válidos (7 dezenas distintas entre 01 e 80) | 2460 |
| Anomalias | 1 — concurso 1307 com 8 dezenas no espelho (fora do recorte; descartado) |
| Confronto com base independente (2.168 concursos) | 0 divergências além do concurso 1307 |
| Último sorteio do recorte | 2.461 · 29/10/2026 · 02–06–17–39–57–64–71 · Inter Limeira/SP |
| Conferência do 2.461 em 4 publicações independentes | dezenas e Time do Coração idênticos |

**Como o acesso foi feito.** A rede onde este levantamento rodou alcança apenas GitHub, PyPI e npm — o domínio `servicebus2.caixa.gov.br` não responde daqui. Para não trabalhar com dados inventados, usei o espelho diário dos resultados oficiais da Caixa publicado em `github.com/eitchtee/loterias.json` (atualizado por GitHub Action todos os dias às 22h de Brasília), e validei:

* contra uma segunda base independente (`github.com/guilhermeasn/loteria.json`, 2.168 concursos) — só o concurso 1307 divergiu;
* contra quatro publicações do concurso 2.461 (dezenas e time idênticos ao espelho).

Para reproduzir contra a API oficial dentro da rede da Caixa, basta trocar a origem do JSON: o script usa um único arquivo de entrada (`dados/timemania_bruto_espelho_caixa.json`) com o mesmo esquema `{concurso, data, resultado[], time_do_coracao}` devolvido por `.../api/timemania/NUMERO`.

**Limitação conhecida da fonte:** o campo "Time do Coração" vem corrompido (caracteres nulos e nomes sobrepostos) nos concursos **1.390 a 1.549**. Nada disso afeta os 100 concursos do recorte, cujos times estão íntegros; a análise de times do histórico completo considera apenas os registros íntegros.

---

## 2. Como cada número foi calculado

| Conceito | Regra adotada |
|---|---|
| **Faixa prevalente** | Menor intervalo contínuo de valores que concentra ≥ 70% dos sorteios do recorte (desempate pela maior cobertura). Ex.: "pares de 3 a 5". |
| **Cobertura** | % de sorteios do recorte que caem dentro da faixa. |
| **IC 95%** | Intervalo de confiança de Wilson para a proporção — mostra a incerteza de uma amostra de 100. |
| **Zebra** | Cauda fora da faixa prevalente, isto é, a fração complementar que ficou de fora dos ~70%. |
| **Validação out-of-sample** | A faixa é recalculada em outra base (histórico completo) e testada no recorte, e vice-versa — evita apresentar regra "sob medida" para 100 sorteios. |
| **Aderência ao uniforme** | χ² com agrupamento de células (esperado ≥ 5) contra a distribuição exata hipergeométrica (e, para a soma, contra a distribuição exata por programação dinâmica sobre C(80,7) = 3.176.716.400 jogos). |

---

## 3. Padrões com prevalência ≥ 70% — recorte dos 100 concursos

### Tabela 1 — Padrões com prevalência ≥ 70% (calibrados no próprio recorte)

| Variável | Faixa / Regra | Cobertura no recorte | IC 95% | Mesma regra no histórico completo |
|---|---|---:|---:|---:|
| Soma das 7 dezenas | 205 – 345 | 70,0% | 60,4% – 78,1% | 76,3% |
| Amplitude (maior − menor) | 53 – 73 | 71,0% | 61,5% – 79,0% | 67,3% |
| Pares | 3 – 5 | 82,0% | 73,3% – 88,3% | 73,0% |
| Baixas (01–40) | 3 – 5 | 72,0% | 62,5% – 79,9% | 73,6% |
| Primos | 1 – 3 | 79,0% | 70,0% – 85,8% | 82,1% |
| Fibonacci | 0 – 1 | 85,0% | 76,7% – 90,7% | 81,3% |
| Múltiplos de 3 | 1 – 3 | 83,0% | 74,5% – 89,1% | 78,7% |
| Maior bloco consecutivo | 1 – 2 | 99,0% | 94,6% – 99,8% | 96,9% |
| Pares adjacentes (n, n+1) | 0 – 1 | 93,0% | 86,3% – 96,6% | 91,7% |
| Faixas de 10 ocupadas (de 8) | 4 – 5 | 75,0% | 65,7% – 82,5% | 70,2% |
| Concentração máx. numa faixa de 10 | 2 – 3 | 93,0% | 86,3% – 96,6% | 93,7% |
| Quadrantes ocupados (de 4) | 3 – 4 | 92,0% | 85,0% – 95,9% | 96,5% |
| Repetidas do concurso anterior | 0 – 1 | 90,0% | 82,6% – 94,5% | 88,7% |
| Terminações distintas | 5 – 6 | 78,0% | 68,9% – 85,0% | 77,3% |
| Terminação mais repetida | 2 | 77,0% | 67,8% – 84,2% | 74,4% |
| Dezenas na moldura do volante | 2 – 4 | 78,0% | 68,9% – 85,0% | 78,3% |
| Dezenas no miolo do volante | 3 – 5 | 78,0% | 68,9% – 85,0% | 78,3% |

**Leitura.** Duas variáveis merecem destaque por serem quase-determinísticas: o **maior bloco consecutivo** raramente passa de 2 (99,0% dos casos) e os **quadrantes ocupados** são 3 ou 4 em 92,0% dos sorteios. Já os que dependem de composição (pares, primos, Fibonacci) concentram-se em faixas estreitas e simétricas em torno do centro, exatamente como o sorteio uniforme produz.

---

## 4. O teste que importa: a mesma regra funciona fora da amostra?

### Tabela 1b — Mesmos padrões calibrados no histórico completo e testados no recorte (out-of-sample)

| Variável | Faixa / Regra | Cobertura no histórico (2.460) | Cobertura no recorte (100) |
|---|---|---:|---:|
| Soma das 7 dezenas | 227 – 347 | 70,2% | 59,0% |
| Amplitude (maior − menor) | 54 – 75 | 70,2% | 73,0% |
| Pares | 2 – 4 | 73,8% | 74,0% |
| Baixas (01–40) | 3 – 5 | 73,6% | 72,0% |
| Primos | 1 – 3 | 82,1% | 79,0% |
| Fibonacci | 0 – 1 | 81,3% | 85,0% |
| Múltiplos de 3 | 1 – 3 | 78,7% | 83,0% |
| Maior bloco consecutivo | 1 – 2 | 96,9% | 99,0% |
| Pares adjacentes (n, n+1) | 0 – 1 | 91,7% | 93,0% |
| Faixas de 10 ocupadas (de 8) | 4 – 5 | 70,2% | 75,0% |
| Concentração máx. numa faixa de 10 | 2 – 3 | 93,7% | 93,0% |
| Quadrantes ocupados (de 4) | 3 – 4 | 96,5% | 92,0% |
| Repetidas do concurso anterior | 0 – 1 | 88,7% | 90,0% |
| Terminações distintas | 5 – 6 | 77,3% | 78,0% |
| Terminação mais repetida | 2 | 74,4% | 77,0% |
| Dezenas na moldura do volante | 2 – 4 | 78,3% | 78,0% |
| Dezenas no miolo do volante | 3 – 5 | 78,3% | 78,0% |

**Leitura.** 16 das 17 variáveis mantêm, no recorte, uma cobertura a menos de 5 pontos percentuais da que tinham no histórico — repetidas 88,7% → 90,0%, primos 82,1% → 79,0%, pares 73,8% → 74,0%, moldura 78,3% → 78,0%. Isso mostra que as faixas **não** são um artefato de calibrar e medir na mesma amostra.

A exceção é a **soma**: a faixa histórica 227–347 cobre 70,2% de 2.460 sorteios, mas apenas 59,0% dos 100 do recorte — 24 sorteios ficaram abaixo de 227 e 17 acima de 347. O motivo é dispersão, não tendência: o desvio-padrão da soma no recorte é 67,2, contra 58,7 no histórico (o valor teórico é 58,7), e a média/mediana seguem no centro da distribuição (280 e 285). Por isso a faixa calibrada no recorte (205–345) é mais larga do que a histórica — é o preço de calibrar com 100 observações.

---

## 5. Zebras — combinações de baixa incidência

### Tabela 2 — Zebras: caudas de baixa incidência (fora do intervalo de ~70%)

| Variável | Faixa / Regra | Cobertura no recorte | Cobertura no histórico |
|---|---|---:|---:|
| Soma das 7 dezenas | 118 – 204 ou 346 – 425 | 30,0% | 22,9% |
| Amplitude (maior − menor) | 26 – 52 ou 74 – 79 | 29,0% | 32,5% |
| Pares | 2 ou 6 | 18,0% | 21,0% |
| Baixas (01–40) | 0 – 2 ou 6 – 7 | 28,0% | 26,4% |
| Primos | 0 ou 4 – 5 | 21,0% | 17,8% |
| Fibonacci | 2 – 3 | 15,0% | 18,3% |
| Múltiplos de 3 | 0 ou 4 – 5 | 17,0% | 20,7% |
| Maior bloco consecutivo | 3 | 1,0% | 2,8% |
| Pares adjacentes (n, n+1) | 2 | 7,0% | 7,1% |
| Faixas de 10 ocupadas (de 8) | 3 ou 6 – 7 | 25,0% | 29,8% |
| Concentração máx. numa faixa de 10 | 1 ou 4 | 7,0% | 6,1% |
| Quadrantes ocupados (de 4) | 2 | 8,0% | 3,5% |
| Repetidas do concurso anterior | 2 | 10,0% | 9,8% |
| Terminações distintas | 3 – 4 ou 7 | 22,0% | 22,7% |
| Terminação mais repetida | 1 ou 3 | 23,0% | 24,4% |
| Dezenas na moldura do volante | 0 – 1 ou 5 – 7 | 22,0% | 21,7% |
| Dezenas no miolo do volante | 0 – 2 ou 6 – 7 | 22,0% | 21,7% |

**Leitura.** As caudas verdadeiramente raras são as de **concentração**: maior bloco consecutivo ≥ 3 (1,0% no recorte, 3,1% no histórico), duas dezenas consecutivas (7,0% / 7,1%), apenas 2 quadrantes ocupados (8,0% / 3,5%) e apenas 1 dezena por faixa de 10 (7,0% / 3,2%).

---

## 6. Repetição — o dado mais sólido da Timemania

### Tabela 3 — Repetição de dezenas do concurso anterior

| Repetidas | Recorte (100) | % | Histórico (2.459) | % | Uniforme (teórico) |
|---|---:|---:|---:|---:|---:|
| 0 | 48 | 48,0% | 1243 | 50,5% | 51,29% |
| 1 | 42 | 42,0% | 939 | 38,2% | 37,51% |
| 2 | 10 | 10,0% | 241 | 9,8% | 9,93% |
| 3 | 0 | 0,0% | 35 | 1,4% | 1,20% |
| 4 | 0 | 0,0% | 1 | 0,0% | 0,07% |

_(0–1 repetida: 90,0% no recorte, 88,7% no histórico, 88,8% teórico)_

**Leitura.** A repetição de 0 a 1 dezena do concurso anterior é mais de 8 em cada 10 sorteios em qualquer base que se olhe — e esse número é a própria previsão do modelo uniforme (88,80%), obtida de C(7,k)·C(73,7−k)/C(80,7). O recorte de 100 concursos teve uma leve inclinação para 1 repetida (42,0% contra 38,2% no histórico), dentro da margem de erro.

### 6.1 Paridade (pares × ímpares)

| Paridade | Recorte (n) | Recorte (%) | Histórico (n) | Histórico (%) | Uniforme (teórico) |
|---|---|---|---|---|---|
| 0P / 7I | 0 | 0,0% | 14 | 0,6% | 0,59% |
| 1P / 6I | 0 | 0,0% | 120 | 4,9% | 4,83% |
| 2P / 5I | 11 | 11,0% | 401 | 16,3% | 16,16% |
| 3P / 4I | 29 | 29,0% | 680 | 27,7% | 28,42% |
| 4P / 3I | 34 | 34,0% | 733 | 29,8% | 28,42% |
| 5P / 2I | 19 | 19,0% | 383 | 15,6% | 16,16% |
| 6P / 1I | 7 | 7,0% | 115 | 4,7% | 4,83% |
| 7P / 0I | 0 | 0,0% | 13 | 0,5% | 0,59% |

Para 7 dezenas sorteadas entre 80 (40 pares, 40 ímpares), o esperado é 3,5 pares. Os três valores centrais (2P, 3P, 4P) respondem por ~73,8% do histórico — e nenhuma paridade fica abaixo de 30% quando medida assim. Os 29,7% e 16,4% citados no anexo são reprodutíveis (29,8% e 16,3%), com uma ressalva importante: **4P/3I não é zebra** — é o valor modal, e o próprio modelo uniforme prevê 28,42% para ele. Já 2P/5I (16,4%) tem previsão teórica de 16,16%: a raridade é estrutural, não uma anomalia da Timemania.

---

## 7. Os sorteios são consistentes com um sorteio justo?

### Tabela 4 — Aderência ao sorteio uniforme (chi-quadrado com células agrupadas)

| Variável | Média observada (100) | Média teórica | χ² recorte | p-valor (100) | p-valor (histórico) |
|---|---:|---:|---:|---:|---:|
| Soma das 7 dezenas | 280,50 | 283,50 | 14,26 (gl 18) | 0,712 | 0,831 |
| Pares | 3,82 | 3,50 | 9,13 (gl 5) | 0,104 | 0,884 |
| Baixas (01–40) | 3,58 | 3,50 | 1,56 (gl 5) | 0,906 | 0,903 |
| Primos | 1,81 | 1,93 | 5,31 (gl 4) | 0,257 | 0,577 |
| Múltiplos de 3 | 2,11 | 2,28 | 3,87 (gl 4) | 0,423 | 0,891 |
| Fibonacci | 0,74 | 0,79 | 0,45 (gl 2) | 0,797 | 0,306 |
| Dezenas na moldura do volante | 2,94 | 2,80 | 3,56 (gl 4) | 0,468 | 0,098 |
| Frequência das 80 dezenas | — | 8,75 por dezena | 63,89 (gl 79) | 0,892 | 0,695 |

**Leitura.** Nenhuma variável se afasta do esperado. A menor margem do recorte é a paridade (p = 0,104), que desaparece no histórico (p = 0,884). A frequência das 80 dezenas é o teste mais duro possível e também não rejeita (p = 0,892 no recorte; 0,695 no histórico): a dezena mais sorteada e a menos sorteada do recorte diferem por algo compatível com ruído binomial.

---

## 8. Dezenas: frequência, faixas e atraso

### Tabela 5 — Frequência das dezenas no recorte (esperado: 8,75 cada)

| Ranking | Dezenas mais sorteadas | Nº | Dezenas menos sorteadas | Nº |
|---|---|---:|---|---:|
| 1º | 52 | 16 | 33 | 4 |
| 2º | 26 | 15 | 39 | 4 |
| 3º | 22 | 14 | 48 | 4 |
| 4º | 80 | 14 | 55 | 4 |
| 5º | 10 | 13 | 61 | 4 |
| 6º | 64 | 13 | 69 | 4 |
| 7º | 76 | 13 | 19 | 5 |
| 8º | 14 | 12 | 41 | 5 |
| 9º | 21 | 12 | 44 | 5 |
| 10º | 36 | 12 | 03 | 6 |

Com 100 concursos, cada dezena deveria aparecer **8,75 vezes**; a observada vai de 4 a 16. O χ² de uniformidade é de 63.89 com 79 graus de liberdade (p = 0.892), isto é, dentro do esperado.

No histórico completo (2460 concursos, 215.2 aparições esperadas por dezena), confirmam-se as dezenas citadas no anexo: **21 (260x), 20 (252x) e 61 (238x)** como mais frequentes, e **53 (172x)** como menos frequente. A diferença entre a primeira e a última (51%) parece grande, mas é o comportamento normal de 80 contagens multinomiais.

### 8.1 Distribuição por faixa de 10 dezenas

| Faixa | Histórico (dezenas) | % das dezenas | Recorte (dezenas) | % das dezenas |
|---|---|---|---|---|
| 01–10 | 2148 | 12,5% | 94 | 13,4% |
| 11–20 | 2184 | 12,7% | 90 | 12,9% |
| 21–30 | 2163 | 12,6% | 99 | 14,1% |
| 31–40 | 2138 | 12,4% | 75 | 10,7% |
| 41–50 | 2142 | 12,4% | 72 | 10,3% |
| 51–60 | 2074 | 12,0% | 97 | 13,9% |
| 61–70 | 2218 | 12,9% | 78 | 11,1% |
| 71–80 | 2146 | 12,5% | 95 | 13,6% |

### Tabela 6 — Dezenas com maior atraso no recorte (sorteios sem aparecer)

| # | Dezena | Atraso | | # | Dezena | Atraso |
|---|---|---:|---|---|---|---:|
| 1º | 37 | 34 | | 6º | 29 | 28 |
| 2º | 35 | 31 | | 7º | 09 | 27 |
| 3º | 48 | 31 | | 8º | 78 | 26 |
| 4º | 63 | 30 | | 9º | 19 | 25 |
| 5º | 43 | 29 | | 10º | 27 | 23 |

**Leitura do atraso.** "Atraso" não é previsão — é apenas quantos sorteios passaram desde a última aparição. Com 80 dezenas e 7 sorteadas por concurso, o atraso máximo esperado entre as 80 fica tipicamente entre 30 e 40 sorteios: ver uma dezena há 30 concursos sem sair é o comportamento normal, não um sinal de que ela "está devendo".

---

## 9. Time do Coração

### Tabela 7 — Time do Coração no recorte (57 times distintos em 100 sorteios)

| Time | Vezes | | Time | Vezes |
|---|---:|---|---|---:|
| ATLETICO/MG | 5 | | CUIABA/MT | 3 |
| TOMBENSE/MG | 5 | | CAXIAS/RS | 3 |
| FLORESTA/CE | 4 | | CRB/AL | 3 |
| VILA NOVA/GO | 3 | | AMERICA/RN | 3 |
| BAHIA/BA | 3 | | VOLTA REDONDA/RJ | 3 |

Repetição do mesmo time em sorteios consecutivos: 4 de 99 (4,0%) — esperado 1,25%.

**Leitura.** 57 times distintos em 100 sorteios é praticamente o que se espera do sorteio uniforme entre 80 clubes (cada um com 1/80 = 1,25%). A repetição do mesmo time em sorteios consecutivos ocorreu 4 vezes em 99 pares (4,0%), contra 1,25% esperados — com amostra desse tamanho, 4 ocorrências ainda são compatíveis com azar (p ≈ 3,6% em teste pontual, que não sobrevive à correção para as comparações feitas).

---

## 10. Últimos 10 sorteios do recorte

### Tabela 8 — Últimos 10 concursos do recorte

| Concurso | Data | Dezenas | Repetidas | Time do Coração |
|---|---|---|---:|---|
| 2461 | 29/10/2026 | 02 – 06 – 17 – 39 – 57 – 64 – 71 | 0 | INTER LIMEIRA/SP |
| 2460 | 27/10/2026 | 03 – 14 – 18 – 24 – 25 – 41 – 70 | 1 | VITORIA/BA |
| 2459 | 24/10/2026 | 16 – 31 – 54 – 59 – 64 – 70 – 73 | 1 | AMERICA/RN |
| 2458 | 22/10/2026 | 14 – 45 – 49 – 52 – 55 – 59 – 80 | 1 | TOMBENSE/MG |
| 2457 | 20/10/2026 | 25 – 28 – 51 – 53 – 56 – 59 – 69 | 0 | PORTO VELHO/RO |
| 2456 | 18/10/2026 | 01 – 16 – 18 – 22 – 41 – 57 – 70 | 0 | ANAPOLIS/GO |
| 2455 | 15/10/2026 | 07 – 28 – 31 – 32 – 60 – 61 – 76 | 0 | LONDRINA/PR |
| 2454 | 13/10/2026 | 03 – 11 – 42 – 46 – 47 – 67 – 79 | 0 | FERROVIARIO/CE |
| 2453 | 11/10/2026 | 02 – 12 – 13 – 17 – 20 – 24 – 30 | 0 | CUIABA/MT |
| 2452 | 08/10/2026 | 39 – 40 – 60 – 62 – 64 – 68 – 72 | 0 | CONFIANCA SAF/SE |

---

## 11. Conferência do anexo original (Timemania)

| Afirmação do anexo | Valor citado | Recalculado nesta base | Situação |
|---|---|---|---|
| Repetidas do anterior: 0 a 1 | 88,7% | 88,7% (histórico) · 90,0% (recorte) | Confere |
| Repetidas do anterior: exatamente 2 | 9,9% | 9,8% (histórico) · 10,0% (recorte) | Confere |
| Repetidas do anterior: 2 ou mais | 9,9% ("3+ não listado") | 11,3% (histórico, incluindo 3 e 4 repetidas) · 10,0% (recorte) | Ajustado: 9,9% é a frequência de exatamente 2; o total de 2 ou mais é 11,3% |
| Paridade 4P/3I | 29,7% | 29,8% (histórico) | Confere |
| Paridade 3P/4I | 27,7% | 27,7% (histórico) | Confere |
| Paridade 2P/5I | 16,4% | 16,3% (histórico) | Confere |
| Dezena mais sorteada: 21 | 242–254 vezes | 260 vezes | Confere (no limite superior) |
| 2ª e 3ª mais sorteadas: 20 e 61 | 241–246 / 228–237 | 252 / 238 vezes | Confere |
| Dezena menos sorteada: 53 | 167 vezes | 172 vezes | Confere (valor corrigido) |
| Faixas de 10 equilibradas | ~2.100–2.145 cada | 2074–2218 cada (esperado 2152) | Confere (desvio máximo de 3% sobre o esperado) |
| Chance de 7 acertos (aposta de 10 dezenas) | 1 em 26.472.637 | C(80,7)/C(10,7) = 3.176.716.400/120 = 26.472.637 | Confere |
| Chance do Time do Coração | 1 em 80 | 80 times possíveis | Confere |
| Times mais sorteados: Atlético-MG (35), Botafogo (33) | — | ATLETICO/GO 46 · BOTAFOGO/RJ 43 · ATLETICO/MG 36 | Parcial: o espelho corrompeu os nomes nos concursos 1.390–1.549 |

*Cuidado ao comparar contagens absolutas:* o anexo usava ~2.421 concursos (até ago/2026); esta base tem 2.460 concursos válidos (até 29/10/2026), o que acrescenta ~39 sorteios e ~273 dezenas — suficiente para deslocar cada contagem em 1 a 10 unidades.

**Conclusão da conferência:** os números centrais do anexo (repetição 0–1 ≈ 88,7%; ≥ 2 ≈ 9,9%; paridade 3P/4I 27,7%; 2P/5I 16,4%) **se confirmam** nesta base, com pequenas correções de casa decimal e com o ajuste de que 4P/3I (29,8%) está no limite de 30% apenas porque é o valor modal, não porque seja raro.

---

## 12. O que esses filtros fazem — e o que não fazem

* **Fazem:** descrever a forma típica de um resultado da Timemania (soma em torno de 283, 3 a 4 dezenas por metade do volante, no máximo 2 consecutivas, 0 a 1 repetida). Isso é útil para **escolher jogos com aparência estatisticamente comum** e para **descartar combinações estruturalmente improváveis** (por exemplo, 7 dezenas seguidas).
* **Não fazem:** aumentar a probabilidade de acerto. Cada combinação de 7 dezenas tem exatamente 1/3.176.716.400; um jogo de 10 dezenas tem 120 combinações e, portanto, 1/26.472.637. Todo jogo que passa nos filtros continua com essa mesma chance — os filtros só reduzem o universo de jogos *e*, na mesma proporção, o número de resultados cobertos.
* **Cuidado com o "0 a 1 repetida":** 88,8% é alto, mas é o valor esperado por azar. Usar "0 a 1 repetida" como filtro elimina ~11% dos resultados possíveis — não aumenta a chance de estar entre eles.
* **Cuidado com múltiplas comparações:** 17 variáveis × 2 bases = 34 testes. Com tantos testes, algum p-valor baixo apareceria por acaso; nenhum apareceu, o que reforça a hipótese de sorteio justo.

---

## 13. Limitações

1. **Tamanho da amostra.** 100 concursos dão IC 95% de ±8 pontos percentuais nas coberturas próximas de 70–90%. Toda a tabela 1 deve ser lida com essa margem.
2. **Fonte espelhada.** O JSON veio de um espelho automatizado da API da Caixa (rede do ambiente bloqueia o domínio da Caixa). Foi validado contra base independente e contra 4 fontes jornalísticas no último concurso, mas para uso oficial a leitura deve ser refeita direto na API.
3. **Time do Coração histórico.** Nomes corrompidos nos concursos 1.390–1.549 do espelho; análise de times do histórico restrita aos registros íntegros.
4. **Mudanças de regra.** A Timemania passou por ajustes de preço e de faixas de premiação; o histórico de 2008–2026 foi tratado como um processo único.
5. **Nada aqui é previsão.** Os números são frequências passadas em um processo sem memória.

---

## 14. Arquivos e reprodutibilidade

| Arquivo | Conteúdo |
|---|---|
| `scripts/analise_timemania.py` | Toda a análise: carga, validação dos dados, 17 variáveis, IC, χ², hipergeométrico, validação cruzada. Só biblioteca padrão do Python 3. |
| `scripts/gerar_relatorio.py` | Monta este relatório a partir das métricas (impede divergência entre texto e tabela). |
| `dados/timemania_bruto_espelho_caixa.json` | Espelho bruto dos resultados oficiais (2.461 concursos, esquema da API da Caixa). |
| `dados/timemania_ultimos_100.csv` | Os 100 concursos do recorte com dezenas, soma, pares, primos, repetidas e time (`;` como separador). |
| `dados/metricas.json` | Todas as métricas, distribuições, p-valores e a série do recorte. |
| `dados/tabelas.md` | Tabelas em markdown exatamente como aparecem aqui. |

```bash
cd analise-timemania
python3 scripts/analise_timemania.py   # recalcula tudo a partir do JSON bruto
python3 scripts/gerar_relatorio.py     # reescreve este relatório
```

---

## 15. Os 100 concursos, sorteio por sorteio

### Tabela 9 — Os 100 concursos do recorte

| Concurso | Data | Dezenas | Rep. | | Concurso | Data | Dezenas | Rep. |
|---|---|---|---:|---|---|---|---:|
| 2362 | 03/03/2026 | 21 26 30 47 51 52 79 | 1 | | 2412 | 07/07/2026 | 09 16 25 47 49 66 73 | 0 |
| 2363 | 05/03/2026 | 04 05 10 14 17 37 67 | 0 | | 2413 | 09/07/2026 | 23 26 35 49 56 60 76 | 1 |
| 2364 | 07/03/2026 | 24 26 31 41 52 54 55 | 0 | | 2414 | 11/07/2026 | 18 19 36 63 64 67 71 | 0 |
| 2365 | 10/03/2026 | 03 07 08 17 29 38 50 | 0 | | 2415 | 14/07/2026 | 04 10 11 21 42 44 69 | 0 |
| 2366 | 12/03/2026 | 08 13 18 22 40 74 76 | 1 | | 2416 | 16/07/2026 | 17 30 36 50 70 74 77 | 0 |
| 2367 | 14/03/2026 | 06 22 28 36 46 52 71 | 1 | | 2417 | 19/07/2026 | 08 12 51 56 72 75 80 | 0 |
| 2368 | 17/03/2026 | 19 24 26 45 66 75 77 | 0 | | 2418 | 21/07/2026 | 12 19 45 67 71 74 76 | 1 |
| 2369 | 19/03/2026 | 21 22 43 59 60 65 73 | 0 | | 2419 | 23/07/2026 | 05 09 12 26 48 52 59 | 1 |
| 2370 | 21/03/2026 | 10 22 40 63 74 76 79 | 1 | | 2420 | 26/07/2026 | 02 14 21 72 76 77 78 | 0 |
| 2371 | 24/03/2026 | 02 16 22 29 32 61 77 | 1 | | 2421 | 28/07/2026 | 07 23 34 37 52 56 65 | 0 |
| 2372 | 26/03/2026 | 12 13 18 23 38 54 55 | 0 | | 2422 | 30/07/2026 | 11 19 21 24 34 68 78 | 1 |
| 2373 | 28/03/2026 | 13 31 33 42 62 65 76 | 1 | | 2423 | 02/08/2026 | 08 25 26 28 50 77 80 | 0 |
| 2374 | 31/03/2026 | 07 28 35 52 57 63 74 | 0 | | 2424 | 04/08/2026 | 11 18 30 32 36 41 60 | 0 |
| 2375 | 02/04/2026 | 01 05 06 09 61 72 74 | 1 | | 2425 | 06/08/2026 | 08 22 41 52 60 62 67 | 2 |
| 2376 | 04/04/2026 | 09 34 38 43 51 63 76 | 1 | | 2426 | 09/08/2026 | 09 16 24 25 44 59 73 | 0 |
| 2377 | 07/04/2026 | 21 35 40 54 58 61 67 | 0 | | 2427 | 11/08/2026 | 03 06 09 24 31 37 71 | 2 |
| 2378 | 09/04/2026 | 10 14 17 21 28 29 36 | 1 | | 2428 | 13/08/2026 | 15 27 49 51 70 76 80 | 0 |
| 2379 | 11/04/2026 | 25 35 48 56 58 75 78 | 0 | | 2429 | 16/08/2026 | 09 18 23 42 47 64 75 | 0 |
| 2380 | 14/04/2026 | 47 54 56 60 64 65 79 | 1 | | 2430 | 18/08/2026 | 21 34 35 38 48 50 64 | 1 |
| 2381 | 16/04/2026 | 04 14 26 32 65 67 68 | 1 | | 2431 | 20/08/2026 | 18 22 55 58 63 65 72 | 0 |
| 2382 | 18/04/2026 | 22 23 30 37 64 68 80 | 1 | | 2432 | 23/08/2026 | 13 43 45 60 64 72 78 | 1 |
| 2383 | 23/04/2026 | 15 36 43 47 54 70 79 | 0 | | 2433 | 25/08/2026 | 06 12 25 28 29 49 80 | 0 |
| 2384 | 25/04/2026 | 14 26 29 47 66 74 79 | 2 | | 2434 | 27/08/2026 | 07 09 38 42 50 52 79 | 0 |
| 2385 | 28/04/2026 | 05 14 16 17 20 70 76 | 1 | | 2435 | 30/08/2026 | 07 15 26 42 53 78 80 | 2 |
| 2386 | 30/04/2026 | 02 20 31 54 59 64 65 | 1 | | 2436 | 01/09/2026 | 19 22 27 28 49 67 73 | 0 |
| 2387 | 05/05/2026 | 03 05 10 27 42 44 52 | 0 | | 2437 | 03/09/2026 | 10 21 26 30 33 51 66 | 0 |
| 2388 | 07/05/2026 | 05 23 27 36 39 46 71 | 2 | | 2438 | 06/09/2026 | 07 27 31 36 66 73 80 | 1 |
| 2389 | 09/05/2026 | 04 06 13 36 47 56 63 | 1 | | 2439 | 08/09/2026 | 01 18 38 50 53 54 57 | 0 |
| 2390 | 12/05/2026 | 04 21 22 36 46 58 78 | 2 | | 2440 | 10/09/2026 | 20 45 51 65 68 77 80 | 0 |
| 2391 | 14/05/2026 | 08 09 16 17 21 71 79 | 1 | | 2441 | 13/09/2026 | 01 02 08 10 56 70 80 | 1 |
| 2392 | 16/05/2026 | 04 12 17 23 59 75 78 | 1 | | 2442 | 15/09/2026 | 26 40 42 47 58 75 80 | 1 |
| 2393 | 19/05/2026 | 14 27 34 46 50 60 73 | 0 | | 2443 | 17/09/2026 | 05 10 17 23 40 49 54 | 1 |
| 2394 | 21/05/2026 | 03 08 15 26 47 52 73 | 1 | | 2444 | 20/09/2026 | 11 21 44 62 64 69 74 | 0 |
| 2395 | 23/05/2026 | 04 10 22 26 32 35 52 | 2 | | 2445 | 22/09/2026 | 07 18 40 46 57 62 76 | 1 |
| 2396 | 26/05/2026 | 01 27 30 37 52 62 68 | 1 | | 2446 | 24/09/2026 | 14 18 30 39 44 52 76 | 2 |
| 2397 | 28/05/2026 | 01 12 15 26 53 64 70 | 1 | | 2447 | 27/09/2026 | 01 10 20 25 30 33 34 | 1 |
| 2398 | 30/05/2026 | 11 29 40 47 48 53 70 | 2 | | 2448 | 29/09/2026 | 32 45 51 60 62 73 75 | 0 |
| 2399 | 02/06/2026 | 02 10 14 33 37 57 62 | 0 | | 2449 | 01/10/2026 | 02 15 20 24 31 56 57 | 0 |
| 2400 | 06/06/2026 | 22 47 51 57 58 64 73 | 1 | | 2450 | 03/10/2026 | 01 05 13 16 30 42 76 | 0 |
| 2401 | 09/06/2026 | 01 08 10 38 40 50 63 | 0 | | 2451 | 06/10/2026 | 04 06 34 38 53 58 69 | 0 |
| 2402 | 11/06/2026 | 38 42 43 63 72 77 78 | 2 | | 2452 | 08/10/2026 | 39 40 60 62 64 68 72 | 0 |
| 2403 | 14/06/2026 | 13 16 36 43 51 65 66 | 1 | | 2453 | 11/10/2026 | 02 12 13 17 20 24 30 | 0 |
| 2404 | 16/06/2026 | 04 11 15 17 23 42 63 | 0 | | 2454 | 13/10/2026 | 03 11 42 46 47 67 79 | 0 |
| 2405 | 18/06/2026 | 09 15 26 52 56 58 80 | 1 | | 2455 | 15/10/2026 | 07 28 31 32 60 61 76 | 0 |
| 2406 | 20/06/2026 | 01 07 20 53 59 75 80 | 1 | | 2456 | 18/10/2026 | 01 16 18 22 41 57 70 | 0 |
| 2407 | 23/06/2026 | 04 07 14 31 52 57 79 | 1 | | 2457 | 20/10/2026 | 25 28 51 53 56 59 69 | 0 |
| 2408 | 25/06/2026 | 08 16 32 36 43 73 79 | 1 | | 2458 | 22/10/2026 | 14 45 49 52 55 59 80 | 1 |
| 2409 | 27/06/2026 | 05 06 10 20 29 67 71 | 0 | | 2459 | 24/10/2026 | 16 31 54 59 64 70 73 | 1 |
| 2410 | 02/07/2026 | 12 22 25 46 53 56 80 | 0 | | 2460 | 27/10/2026 | 03 14 18 24 25 41 70 | 1 |
| 2411 | 04/07/2026 | 20 31 35 51 56 59 79 | 1 | | 2461 | 29/10/2026 | 02 06 17 39 57 64 71 | 0 |

---

## Apêndice — distribuição completa das variáveis no recorte

- **Soma das 7 dezenas** — min 118, mediana 285, média 280,5, máx 425 | contagem por valor → 118: 1, 152: 1, 153: 1, 154: 1, 155: 1, 175: 1, 181: 2, 183: 2, 195: 1, 198: 1, 201: 1, 205: 1, 208: 1, 210: 1, 211: 1, 213: 1, 215: 1, 218: 1, 221: 1, 224: 1, 225: 2, 227: 1, 228: 2, 229: 1, 237: 1, 239: 1, 241: 1, 244: 1, 247: 1, 250: 1, 251: 1, 255: 1, 256: 1, 261: 1, 262: 1, 265: 1, 268: 1, 271: 1, 273: 1, 274: 1, 276: 1, 277: 2, 278: 1, 283: 1, 285: 2, 287: 1, 290: 2, 294: 2, 295: 4, 296: 1, 298: 1, 301: 1, 304: 1, 306: 2, 312: 1, 314: 1, 316: 1, 320: 1, 322: 1, 324: 1, 325: 1, 331: 1, 332: 1, 335: 1, 336: 1, 338: 1, 340: 1, 341: 1, 343: 1, 344: 1, 345: 1, 353: 1, 354: 3, 364: 2, 367: 1, 368: 2, 372: 1, 375: 2, 398: 1, 405: 1, 406: 1, 413: 1, 425: 1
- **Amplitude (maior − menor)** — min 26, mediana 63,5, média 60,5, máx 79 | contagem por valor → 26: 1, 28: 1, 31: 1, 32: 1, 33: 2, 40: 1, 43: 3, 44: 1, 46: 1, 47: 1, 48: 1, 49: 3, 51: 1, 52: 1, 53: 4, 54: 4, 55: 1, 56: 2, 57: 1, 58: 4, 59: 6, 60: 3, 62: 2, 63: 4, 64: 5, 65: 6, 66: 4, 67: 5, 68: 3, 69: 6, 70: 1, 71: 4, 72: 3, 73: 3, 74: 3, 75: 3, 76: 2, 79: 2
- **Pares** — min 2, mediana 4, média 3,8, máx 6 | contagem por valor → 2: 11, 3: 29, 4: 34, 5: 19, 6: 7
- **Baixas (01–40)** — min 0, mediana 4, média 3,6, máx 7 | contagem por valor → 0: 1, 1: 6, 2: 14, 3: 27, 4: 27, 5: 18, 6: 4, 7: 3
- **Primos** — min 0, mediana 2, média 1,8, máx 5 | contagem por valor → 0: 15, 1: 26, 2: 29, 3: 24, 4: 5, 5: 1
- **Fibonacci** — min 0, mediana 1, média 0,7, máx 3 | contagem por valor → 0: 43, 1: 42, 2: 13, 3: 2
- **Múltiplos de 3** — min 0, mediana 2, média 2,1, máx 5 | contagem por valor → 0: 8, 1: 21, 2: 33, 3: 29, 4: 8, 5: 1
- **Maior bloco consecutivo** — min 1, mediana 1, média 1,4, máx 3 | contagem por valor → 1: 63, 2: 36, 3: 1
- **Pares adjacentes (n, n+1)** — min 0, mediana 0, média 0,4, máx 2 | contagem por valor → 0: 63, 1: 30, 2: 7
- **Faixas de 10 ocupadas (de 8)** — min 3, mediana 5, média 4,9, máx 7 | contagem por valor → 3: 3, 4: 28, 5: 47, 6: 21, 7: 1
- **Concentração máx. numa faixa de 10** — min 1, mediana 2, média 2,4, máx 4 | contagem por valor → 1: 1, 2: 61, 3: 32, 4: 6
- **Quadrantes ocupados (de 4)** — min 2, mediana 4, média 3,4, máx 4 | contagem por valor → 2: 8, 3: 41, 4: 51
- **Repetidas do concurso anterior** — min 0, mediana 1, média 0,6, máx 2 | contagem por valor → 0: 48, 1: 42, 2: 10
- **Terminações distintas** — min 3, mediana 5, média 5,4, máx 7 | contagem por valor → 3: 1, 4: 12, 5: 38, 6: 40, 7: 9
- **Terminação mais repetida** — min 1, mediana 2, média 2,0, máx 3 | contagem por valor → 1: 9, 2: 77, 3: 14
- **Dezenas na moldura do volante** — min 0, mediana 3, média 2,9, máx 7 | contagem por valor → 0: 1, 1: 9, 2: 30, 3: 31, 4: 17, 5: 9, 6: 2, 7: 1
- **Dezenas no miolo do volante** — min 0, mediana 4, média 4,1, máx 7 | contagem por valor → 0: 1, 1: 2, 2: 9, 3: 17, 4: 31, 5: 30, 6: 9, 7: 1
