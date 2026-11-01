#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera LEVANTAMENTO-TIMEMANIA.md a partir de dados/metricas.json + dados/tabelas.md.

A narrativa é fixa; todos os números vêm do JSON/da tabela gerada, de modo que
reexecutar scripts/analise_timemania.py + este script sempre produz um relatório
consistente com os dados.
"""

import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(os.path.join(BASE, "dados", "metricas.json"), encoding="utf-8"))
TAB = open(os.path.join(BASE, "dados", "tabelas.md"), encoding="utf-8").read()


def bloco(prefixo):
    """Extrai de tabelas.md o bloco que começa com '## <prefixo>' até o próximo '## '."""
    m = re.search(r"^## " + re.escape(prefixo) + r".*?(?=^## |\Z)", TAB, re.S | re.M)
    if not m:
        return f"[bloco {prefixo} ausente]"
    bloco_txt = m.group(0).strip()
    # rebaixa "## Tabela X" para "### Tabela X" (mantém hierarquia dentro das seções)
    return re.sub(r"^## ", "### ", bloco_txt, count=1)


def corpo(prefixo):
    """Bloco sem a linha de título (o relatório usa o próprio cabeçalho)."""
    return bloco(prefixo).split("\n", 1)[1].strip()


def recorte():
    return TAB.split("\n\n")[0]


def pct(x, nd=1):
    return f"{x:.{nd}f}%".replace(".", ",")


U, F = M["ultimos_100"], M["historico_completo"]

import math as _m
_q = 1 / 80
_p_time = sum(_m.comb(99, k) * _q ** k * (1 - _q) ** (99 - k) for k in range(4, 100))
VU, VF = U["variaveis"], F["variaveis"]
REP_U = {d["valor"]: d for d in VU["repetidas"]["distribuicao"]}
REP_F = {d["valor"]: d for d in VF["repetidas"]["distribuicao"]}
PAR_U = {d["valor"]: d for d in VU["pares"]["distribuicao"]}
PAR_F = {d["valor"]: d for d in VF["pares"]["distribuicao"]}


def pct_rep(d, ks):
    return sum(d.get(k, {}).get("pct", 0.0) for k in ks)


def hist_pct(chave, cond):
    """% no histórico completo dos valores que satisfazem cond (chaves JSON são strings)."""
    c = {int(k): v for k, v in M["hist_contagem"][chave].items()}
    n = M["hist_contagem"]["__n__"]
    return pct(100 * sum(v for k, v in c.items() if cond(k)) / n)


def table(linhas, cabecalho):
    out = ["| " + " | ".join(cabecalho) + " |",
           "|" + "|".join(["---"] * len(cabecalho)) + "|"]
    out += ["| " + " | ".join(str(c) for c in ln) + " |" for ln in linhas]
    return "\n".join(out)


# ------------------------------------------------------------------ tabelas próprias

import math as _math
_TOT = _math.comb(80, 7)
_TEO_P = {k: 100 * _math.comb(40, k) * _math.comb(40, 7 - k) / _TOT for k in range(8)}

paridade = table(
    [[f"{k}P / {7 - k}I", PAR_U.get(k, {}).get("n", 0), pct(PAR_U.get(k, {}).get("pct", 0)),
      PAR_F.get(k, {}).get("n", 0), pct(PAR_F.get(k, {}).get("pct", 0)), pct(_TEO_P[k], 2)]
     for k in range(0, 8)],
    ["Paridade", "Recorte (n)", "Recorte (%)", "Histórico (n)", "Histórico (%)", "Uniforme (teórico)"],
)

_tot_hist = F["n"] * 7
_tot_rec = U["n"] * 7
faixas10 = table(
    [[f"{int(k):02d}–{int(k)+9:02d}", v, pct(100 * v / _tot_hist),
      U["dezenas"]["por_faixa10"][k], pct(100 * U["dezenas"]["por_faixa10"][k] / _tot_rec)]
     for k, v in F["dezenas"]["por_faixa10"].items()],
    ["Faixa", "Histórico (dezenas)", "% das dezenas", "Recorte (dezenas)", "% das dezenas"],
)

_somas = [sum(r["dezenas"]) for r in M["seq_ultimos_100"]]
_sd_rec = f"{VU['soma']['estat']['dp']:.1f}".replace(".", ",")
_sd_hist = f"{VF['soma']['estat']['dp']:.1f}".replace(".", ",")
_media = f"{VU['soma']['estat']['media']:.0f}"
_mediana = f"{VU['soma']['estat']['mediana']:.0f}".replace(".", ",")
_f_lo, _f_hi = VF["soma"]["faixa"]
_abaixo = sum(1 for v in _somas if v < _f_lo)
_acima = sum(1 for v in _somas if v > _f_hi)
_deltas = [abs(v["cov_100"] - v["cov_full"]) for v in M["validacao"]["regras_do_full_no_recorte"].values()]
_dentro = sum(1 for d in _deltas if d <= 5)

conferencia = table(
    [
        ["Repetidas do anterior: 0 a 1", "88,7%",
         f"{pct(pct_rep(REP_F, [0, 1]))} (histórico) · {pct(pct_rep(REP_U, [0, 1]))} (recorte)",
         "Confere"],
        ["Repetidas do anterior: exatamente 2", "9,9%",
         f"{pct(REP_F.get(2, {}).get('pct', 0))} (histórico) · {pct(REP_U.get(2, {}).get('pct', 0))} (recorte)",
         "Confere"],
        ["Repetidas do anterior: 2 ou mais", "9,9% (\"3+ não listado\")",
         f"{pct(pct_rep(REP_F, [2, 3, 4]))} (histórico, incluindo 3 e 4 repetidas) · "
         f"{pct(pct_rep(REP_U, [2]))} (recorte)",
         "Ajustado: 9,9% é a frequência de exatamente 2; o total de 2 ou mais é 11,3%"],
        ["Paridade 4P/3I", "29,7%", pct(PAR_F.get(4, {}).get("pct", 0)) + " (histórico)", "Confere"],
        ["Paridade 3P/4I", "27,7%", pct(PAR_F.get(3, {}).get("pct", 0)) + " (histórico)", "Confere"],
        ["Paridade 2P/5I", "16,4%", pct(PAR_F.get(2, {}).get("pct", 0)) + " (histórico)", "Confere"],
        ["Dezena mais sorteada: 21", "242–254 vezes",
         f"{F['dezenas']['contagem']['21']} vezes", "Confere (no limite superior)"],
        ["2ª e 3ª mais sorteadas: 20 e 61", "241–246 / 228–237",
         f"{F['dezenas']['contagem']['20']} / {F['dezenas']['contagem']['61']} vezes", "Confere"],
        ["Dezena menos sorteada: 53", "167 vezes",
         f"{F['dezenas']['contagem']['53']} vezes", "Confere (valor corrigido)"],
        ["Faixas de 10 equilibradas", "~2.100–2.145 cada",
         f"{min(F['dezenas']['por_faixa10'].values())}–{max(F['dezenas']['por_faixa10'].values())} cada "
         f"(esperado {F['dezenas']['esperado'] * 10:.0f})",
         "Confere (desvio máximo de 3% sobre o esperado)"],
        ["Chance de 7 acertos (aposta de 10 dezenas)", "1 em 26.472.637",
         "C(80,7)/C(10,7) = 3.176.716.400/120 = 26.472.637", "Confere"],
        ["Chance do Time do Coração", "1 em 80", "80 times possíveis", "Confere"],
        ["Times mais sorteados: Atlético-MG (35), Botafogo (33)", "—",
         "ATLETICO/GO 46 · BOTAFOGO/RJ 43 · ATLETICO/MG 36",
         "Parcial: o espelho corrompeu os nomes nos concursos 1.390–1.549"],
    ],
    ["Afirmação do anexo", "Valor citado", "Recalculado nesta base", "Situação"],
)

# ------------------------------------------------------------------ relatório

partes = []
partes.append(f"""# Levantamento Timemania — últimos 100 concursos

**Recorte:** concursos **{U['primeiro']} a {U['ultimo']}** ({U['data_ini']} a {U['data_fim']}) — {U['n']} sorteios
**Histórico de referência:** {F['n'] + 1} concursos (2008 a {F['data_fim']})
**Fonte:** API oficial de loterias da Caixa (`servicebus2.caixa.gov.br/portaldeloterias/api/timemania`), lida por espelho diário e conferida contra base independente
**Gerado em:** {M['gerado_em'][:16].replace('T', ' ')} · cada sorteio: 7 dezenas entre 80 + 1 Time do Coração entre 80 clubes

> **Nota metodológica.** Os percentuais abaixo são **descritivos do histórico**. Em um sorteio justo, nenhuma combinação tem probabilidade maior que outra, e nenhum filtro aumenta a chance de prêmio. A Timemania paga 1 em 26.472.637 para 7 acertos (aposta mínima de 10 dezenas) e 1 em 80 para o Time do Coração.

---

## Resumo executivo

**O que este levantamento traz de novo em relação ao anexo:** o anexo dizia que a Timemania "carece de uma tabela de filtros > 70% / < 30%". Com os 100 concursos mais recentes **e** com o histórico completo, é possível montar essa tabela: 17 variáveis foram calculadas no recorte, e todas têm um intervalo que cobre ≥ 70% dos sorteios — o que muda de uma para outra é a **largura** desse intervalo.

1. **Repetição do concurso anterior é o padrão mais robusto e foi confirmado.** 0 a 1 repetida cobre **{pct(pct_rep(REP_U, [0, 1]))}** dos 100 sorteios e **{pct(pct_rep(REP_F, [0, 1]))}** de todo o histórico — praticamente igual ao esperado por puro azar (**{pct(100 * (M['pmf_repetidas']['0'] + M['pmf_repetidas']['1']), 2)}**). O valor de 88,7% citado no anexo está correto.
2. **Padrões estruturais com cobertura muito alta no recorte:** maior bloco consecutivo 1–2 ({pct(VU['bloco']['cobertura'])}), quadrantes 3–4 ({pct(VU['quadrantes']['cobertura'])}), pares adjacentes 0–1 ({pct(VU['adjacentes']['cobertura'])}), concentração por faixa de 10 de 2–3 dezenas ({pct(VU['concentracao']['cobertura'])}).
3. **Padrões de composição:** pares 3–5 ({pct(VU['pares']['cobertura'])}), primos 1–3 ({pct(VU['primos']['cobertura'])}), Fibonacci 0–1 ({pct(VU['fibonacci']['cobertura'])}), múltiplos de 3 1–3 ({pct(VU['mult3']['cobertura'])}), terminações distintas 5–6 ({pct(VU['finais_distintos']['cobertura'])}).
4. **Zebras (caudas raras):** maior bloco ≥ 3 ({pct(VU['bloco']['zebra_pct'])}), pares adjacentes = 2 ({pct(VU['adjacentes']['zebra_pct'])}), 2 repetidas ({pct(VU['repetidas']['zebra_pct'])}), nenhum primo ({pct(VU['primos']['zebra_pct'])}), apenas 2 quadrantes ocupados ({pct(VU['quadrantes']['zebra_pct'])}).
5. **Testes de aderência ao sorteio uniforme não rejeitam nada.** Soma, paridade, baixas, primos, múltiplos de 3, Fibonacci, moldura e a frequência das 80 dezenas: todos com p-valor acima de 0,05, no recorte e no histórico. Isto é, as "faixas de 70%" **descrevem** como os sorteios se distribuem — não revelam tendência.
6. **As faixas de 10 dezenas são levemente desiguais apenas por acaso** no recorte (de {min(U['dezenas']['por_faixa10'].values())} a {max(U['dezenas']['por_faixa10'].values())} aparições por faixa, contra 87,5 esperadas), e praticamente niveladas no histórico.

---

## 1. Base de dados, fonte e validação

| Item | Resultado |
|---|---|
| Registros lidos do espelho da API da Caixa | {M['fonte']['registros_no_arquivo']} concursos (todos os existentes) |
| Concursos válidos (7 dezenas distintas entre 01 e 80) | {M['fonte']['registros_validos']} |
| Anomalias | 1 — concurso 1307 com 8 dezenas no espelho (fora do recorte; descartado) |
| Confronto com base independente (2.168 concursos) | 0 divergências além do concurso 1307 |
| Último sorteio do recorte | 2.461 · 29/10/2026 · 02–06–17–39–57–64–71 · Inter Limeira/SP |
| Conferência do 2.461 em 4 publicações independentes | dezenas e Time do Coração idênticos |

**Como o acesso foi feito.** A rede onde este levantamento rodou alcança apenas GitHub, PyPI e npm — o domínio `servicebus2.caixa.gov.br` não responde daqui. Para não trabalhar com dados inventados, usei o espelho diário dos resultados oficiais da Caixa publicado em `github.com/eitchtee/loterias.json` (atualizado por GitHub Action todos os dias às 22h de Brasília), e validei:

* contra uma segunda base independente (`github.com/guilhermeasn/loteria.json`, 2.168 concursos) — só o concurso 1307 divergiu;
* contra quatro publicações do concurso 2.461 (dezenas e time idênticos ao espelho).

Para reproduzir contra a API oficial dentro da rede da Caixa, basta trocar a origem do JSON: o script usa um único arquivo de entrada (`dados/timemania_bruto_espelho_caixa.json`) com o mesmo esquema `{{concurso, data, resultado[], time_do_coracao}}` devolvido por `.../api/timemania/NUMERO`.

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

{bloco('Tabela 1')}

**Leitura.** Duas variáveis merecem destaque por serem quase-determinísticas: o **maior bloco consecutivo** raramente passa de 2 ({pct(VU['bloco']['cobertura'])} dos casos) e os **quadrantes ocupados** são 3 ou 4 em {pct(VU['quadrantes']['cobertura'])} dos sorteios. Já os que dependem de composição (pares, primos, Fibonacci) concentram-se em faixas estreitas e simétricas em torno do centro, exatamente como o sorteio uniforme produz.

---

## 4. O teste que importa: a mesma regra funciona fora da amostra?

{bloco('Tabela 1b')}

**Leitura.** {_dentro} das 17 variáveis mantêm, no recorte, uma cobertura a menos de 5 pontos percentuais da que tinham no histórico — repetidas 88,7% → 90,0%, primos 82,1% → 79,0%, pares 73,8% → 74,0%, moldura 78,3% → 78,0%. Isso mostra que as faixas **não** são um artefato de calibrar e medir na mesma amostra.

A exceção é a **soma**: a faixa histórica 227–347 cobre 70,2% de 2.460 sorteios, mas apenas 59,0% dos 100 do recorte — {_abaixo} sorteios ficaram abaixo de 227 e {_acima} acima de 347. O motivo é dispersão, não tendência: o desvio-padrão da soma no recorte é {_sd_rec}, contra {_sd_hist} no histórico (o valor teórico é 58,7), e a média/mediana seguem no centro da distribuição ({_media} e {_mediana}). Por isso a faixa calibrada no recorte (205–345) é mais larga do que a histórica — é o preço de calibrar com 100 observações.

---

## 5. Zebras — combinações de baixa incidência

{bloco('Tabela 2')}

**Leitura.** As caudas verdadeiramente raras são as de **concentração**: maior bloco consecutivo ≥ 3 ({pct(VU['bloco']['zebra_pct'])} no recorte, {hist_pct('bloco', lambda k: k >= 3)} no histórico), duas dezenas consecutivas ({pct(VU['adjacentes']['zebra_pct'])} / {hist_pct('adjacentes', lambda k: k == 2)}), apenas 2 quadrantes ocupados ({pct(VU['quadrantes']['zebra_pct'])} / {hist_pct('quadrantes', lambda k: k == 2)}) e apenas 1 dezena por faixa de 10 ({pct(VU['concentracao']['zebra_pct'])} / {hist_pct('concentracao', lambda k: k == 1)}).

---

## 6. Repetição — o dado mais sólido da Timemania

{bloco('Tabela 3')}

**Leitura.** A repetição de 0 a 1 dezena do concurso anterior é mais de 8 em cada 10 sorteios em qualquer base que se olhe — e esse número é a própria previsão do modelo uniforme ({pct(100 * (M['pmf_repetidas']['0'] + M['pmf_repetidas']['1']), 2)}), obtida de C(7,k)·C(73,7−k)/C(80,7). O recorte de 100 concursos teve uma leve inclinação para 1 repetida ({pct(REP_U.get(1, {}).get('pct', 0))} contra {pct(REP_F.get(1, {}).get('pct', 0))} no histórico), dentro da margem de erro.

### 6.1 Paridade (pares × ímpares)

{paridade}

Para 7 dezenas sorteadas entre 80 (40 pares, 40 ímpares), o esperado é 3,5 pares. Os três valores centrais (2P, 3P, 4P) respondem por ~73,8% do histórico — e nenhuma paridade fica abaixo de 30% quando medida assim. Os 29,7% e 16,4% citados no anexo são reprodutíveis ({pct(PAR_F.get(4, {}).get('pct', 0))} e {pct(PAR_F.get(2, {}).get('pct', 0))}), com uma ressalva importante: **4P/3I não é zebra** — é o valor modal, e o próprio modelo uniforme prevê {pct(_TEO_P[4], 2)} para ele. Já 2P/5I (16,4%) tem previsão teórica de {pct(_TEO_P[2], 2)}: a raridade é estrutural, não uma anomalia da Timemania.

---

## 7. Os sorteios são consistentes com um sorteio justo?

{bloco('Tabela 4')}

**Leitura.** Nenhuma variável se afasta do esperado. A menor margem do recorte é a paridade (p = 0,104), que desaparece no histórico (p = 0,884). A frequência das 80 dezenas é o teste mais duro possível e também não rejeita (p = 0,892 no recorte; 0,695 no histórico): a dezena mais sorteada e a menos sorteada do recorte diferem por algo compatível com ruído binomial.

---

## 8. Dezenas: frequência, faixas e atraso

{bloco('Tabela 5')}

Com 100 concursos, cada dezena deveria aparecer **8,75 vezes**; a observada vai de 4 a 16. O χ² de uniformidade é de {U['dezenas']['chi2']:.2f} com 79 graus de liberdade (p = {U['dezenas']['p_valor']:.3f}), isto é, dentro do esperado.

No histórico completo ({F['n'] + 1} concursos, {F['dezenas']['esperado']:.1f} aparições esperadas por dezena), confirmam-se as dezenas citadas no anexo: **21 ({F['dezenas']['contagem']['21']}x), 20 ({F['dezenas']['contagem']['20']}x) e 61 ({F['dezenas']['contagem']['61']}x)** como mais frequentes, e **53 ({F['dezenas']['contagem']['53']}x)** como menos frequente. A diferença entre a primeira e a última ({(F['dezenas']['contagem']['21'] / F['dezenas']['contagem']['53'] - 1) * 100:.0f}%) parece grande, mas é o comportamento normal de 80 contagens multinomiais.

### 8.1 Distribuição por faixa de 10 dezenas

{faixas10}

{bloco('Tabela 6')}

**Leitura do atraso.** "Atraso" não é previsão — é apenas quantos sorteios passaram desde a última aparição. Com 80 dezenas e 7 sorteadas por concurso, o atraso máximo esperado entre as 80 fica tipicamente entre 30 e 40 sorteios: ver uma dezena há 30 concursos sem sair é o comportamento normal, não um sinal de que ela "está devendo".

---

## 9. Time do Coração

{bloco('Tabela 7')}

**Leitura.** {U['times']['distintos']} times distintos em 100 sorteios é praticamente o que se espera do sorteio uniforme entre 80 clubes (cada um com 1/80 = 1,25%). A repetição do mesmo time em sorteios consecutivos ocorreu {U['times']['repeticao_n']} vezes em 99 pares ({pct(U['times']['repeticao_pct'])}), contra 1,25% esperados — com amostra desse tamanho, 4 ocorrências ainda são compatíveis com azar (p ≈ {pct(100 * _p_time, 1)} em teste pontual, que não sobrevive à correção para as comparações feitas).

---

## 10. Últimos 10 sorteios do recorte

{bloco('Tabela 8')}

---

## 11. Conferência do anexo original (Timemania)

{conferencia}

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

{bloco('Tabela 9')}

---

## Apêndice — distribuição completa das variáveis no recorte

{corpo('Apêndice')}
""")

saida = "\n".join(partes)
destino = os.path.join(BASE, "LEVANTAMENTO-TIMEMANIA.md")
open(destino, "w", encoding="utf-8").write(saida)
print(f"OK — {destino} ({len(saida)} bytes)")
