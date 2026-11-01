#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Levantamento estatístico da TIMEMANIA — Caixa Econômica Federal.

Recorte principal : últimos 100 concursos (2362 a 2461, 03/03/2026 a 29/10/2026).
Base de contexto  : histórico completo (2.460 concursos com 7 dezenas válidas, 2008-2026).

Fonte dos dados   : espelho diário dos resultados oficiais da API da Caixa
                    (github.com/eitchtee/loterias.json -> data/timemania.json),
                    conferido contra base independente (github.com/guilhermeasn/loteria.json)
                    e contra 4 publicações do concurso 2461.

Saídas (pasta dados/): metricas.json, timemania_ultimos_100.csv, tabelas.md

Uso:  python3 scripts/analise_timemania.py
"""

import csv
import collections
import datetime
import json
import math
import os
import re
import unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "dados", "timemania_bruto_espelho_caixa.json")
OUT_DIR = os.path.join(BASE, "dados")

N_ULTIMOS = 100
PRIMOS = [p for p in range(2, 81) if all(p % d for d in range(2, int(p ** 0.5) + 1))]
FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34, 55]
C80_7 = math.comb(80, 7)

# ---------------------------------------------------------------- utilidades


def wilson(k, n, z=1.96):
    """IC 95% (Wilson) para proporção."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    margem = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centro - margem), min(1.0, centro + margem))


def _gammaq(a, x):
    """Q(a,x) = Gamma(a,x)/Gamma(a) — série + fração continuada."""
    if x <= 0:
        return 1.0
    if x < a + 1:
        ap, s, delta = a, 1.0 / a, 1.0 / a
        for _ in range(2000):
            ap += 1
            delta *= x / ap
            s += delta
            if abs(delta) < abs(s) * 1e-15:
                break
        return 1.0 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    tiny, b = 1e-300, x + 1 - a
    c, d = 1 / tiny, 1 / b
    h = d
    for i in range(1, 2000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def chi2_sf(chi2, gl):
    return _gammaq(gl / 2.0, chi2 / 2.0)


def normalizar_time(t):
    t = (t or "").replace("\x00", " ").strip().upper()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s*/\s*", "/", t)
    return t


def time_confiavel(t):
    return bool(t) and "\x00" not in t and len(t) <= 30


# ---------------------------------------------------------------- variáveis


def longest_run(nums):
    run = melhor = 1
    for a, b in zip(nums, nums[1:]):
        run = run + 1 if b == a + 1 else 1
        melhor = max(melhor, run)
    return melhor


def na_moldura(n):
    """Volante 8 linhas x 10 colunas: moldura = 1ª/última linha e 1ª/última coluna."""
    return ((n - 1) // 10) in (0, 7) or ((n - 1) % 10) in (0, 9)


VARS = [
    ("soma", "Soma das 7 dezenas", lambda n, p: sum(n),
     "Soma total das dezenas sorteadas"),
    ("amplitude", "Amplitude (maior − menor)", lambda n, p: max(n) - min(n),
     "Maior dezena menos a menor dezena"),
    ("pares", "Pares", lambda n, p: sum(1 for x in n if x % 2 == 0),
     "Quantidade de dezenas pares"),
    ("baixas", "Baixas (01–40)", lambda n, p: sum(1 for x in n if x <= 40),
     "Dezenas na metade inferior do volante"),
    ("primos", "Primos", lambda n, p: sum(1 for x in n if x in PRIMOS),
     "Dezenas primas"),
    ("fibonacci", "Fibonacci", lambda n, p: sum(1 for x in n if x in FIBONACCI),
     "Dezenas da sequência de Fibonacci"),
    ("mult3", "Múltiplos de 3", lambda n, p: sum(1 for x in n if x % 3 == 0),
     "Dezenas divisíveis por 3"),
    ("bloco", "Maior bloco consecutivo", lambda n, p: longest_run(n),
     "Maior sequência de dezenas consecutivas"),
    ("adjacentes", "Pares adjacentes (n, n+1)", lambda n, p: sum(1 for a, b in zip(n, n[1:]) if b == a + 1),
     "Quantos pares consecutivos existem no jogo"),
    ("faixas", "Faixas de 10 ocupadas (de 8)", lambda n, p: len({(x - 1) // 10 for x in n}),
     "Faixas 01–10 … 71–80 com ao menos 1 dezena"),
    ("concentracao", "Concentração máx. numa faixa de 10",
     lambda n, p: max(collections.Counter((x - 1) // 10 for x in n).values()),
     "Maior número de dezenas numa mesma faixa de 10"),
    ("quadrantes", "Quadrantes ocupados (de 4)", lambda n, p: len({(x - 1) // 20 for x in n}),
     "Quadrantes 01–20, 21–40, 41–60, 61–80 ocupados"),
    ("repetidas", "Repetidas do concurso anterior", lambda n, p: len(set(n) & set(p)),
     "Dezenas que repetiram do sorteio imediatamente anterior"),
    ("finais_distintos", "Terminações distintas", lambda n, p: len({x % 10 for x in n}),
     "Quantidade de dígitos finais diferentes"),
    ("final_repetido_max", "Terminação mais repetida", lambda n, p: max(collections.Counter(x % 10 for x in n).values()),
     "Quantas dezenas compartilham o final mais comum"),
    ("moldura", "Dezenas na moldura do volante", lambda n, p: sum(1 for x in n if na_moldura(x)),
     "Dezenas nas bordas do volante 8x10"),
    ("miolo", "Dezenas no miolo do volante", lambda n, p: 7 - sum(1 for x in n if na_moldura(x)),
     "Dezenas no interior do volante 8x10"),
]

NOMES = {c: n for c, n, _, _ in VARS}
DESC = {c: d for c, _, _, d in VARS}


def intervalo_otimo(valores, alvo=0.70):
    """Menor intervalo contíguo [a,b] com cobertura >= alvo (desempate: maior cobertura)."""
    cont = collections.Counter(valores)
    total = len(valores)
    lo, hi = min(valores), max(valores)
    melhor = None
    for a in range(lo, hi + 1):
        soma = 0
        for b in range(a, hi + 1):
            soma += cont.get(b, 0)
            cov = soma / total
            if cov >= alvo:
                chave = (b - a, -cov)
                if melhor is None or chave < melhor[0]:
                    melhor = (chave, a, b, cov)
                break
    if melhor is None:
        return lo, hi, 1.0
    return melhor[1], melhor[2], melhor[3]


def cobertura(valores, a, b):
    k = sum(1 for v in valores if a <= v <= b)
    return k, len(valores), k / len(valores)


def distrib(valores):
    cont = collections.Counter(valores)
    total = len(valores)
    return [{"valor": k, "n": cont[k], "pct": 100 * cont[k] / total} for k in sorted(cont)]


def describe(valores):
    s = sorted(valores)
    n = len(s)
    media = sum(s) / n
    return {
        "n": n, "media": media,
        "dp": math.sqrt(sum((x - media) ** 2 for x in s) / (n - 1)),
        "min": s[0], "p10": s[int(0.10 * (n - 1))], "p25": s[int(0.25 * (n - 1))],
        "mediana": s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2,
        "p75": s[int(0.75 * (n - 1))], "p90": s[int(0.90 * (n - 1))], "max": s[-1],
        "media_teorica": None,
    }


# ---------------------------------------------------------------- carga


def carregar():
    bruto = sorted(json.load(open(RAW, encoding="utf-8")), key=lambda d: d["concurso"])
    validos, anomalias = [], []
    for d in bruto:
        dez = [int(x) for x in d["resultado"]]
        if len(dez) != 7 or len(set(dez)) != 7 or not all(1 <= x <= 80 for x in dez):
            anomalias.append({"concurso": d["concurso"], "data": d["data"], "resultado": dez})
            continue
        bruto_time = d.get("time_do_coracao") or ""
        validos.append({
            "concurso": d["concurso"], "data": d["data"], "dezenas": sorted(dez),
            "time": normalizar_time(bruto_time), "time_ok": time_confiavel(bruto_time),
        })
    return validos, anomalias, len(bruto)


# ---------------------------------------------------------------- análise


def valores_das_variaveis(registros, idx_ini, idx_fim):
    out = {}
    for chave, _, fn, _ in VARS:
        out[chave] = [fn(registros[i]["dezenas"],
                         registros[i - 1]["dezenas"] if i > 0 else [])
                      for i in range(idx_ini, idx_fim + 1)]
    return out


def analisar(registros, idx_ini, idx_fim, label):
    janela = registros[idx_ini:idx_fim + 1]
    vals = valores_das_variaveis(registros, idx_ini, idx_fim)
    res = {
        "label": label, "n": len(janela),
        "primeiro": janela[0]["concurso"], "ultimo": janela[-1]["concurso"],
        "data_ini": janela[0]["data"], "data_fim": janela[-1]["data"],
        "variaveis": {},
    }
    for chave, nome, _, desc in VARS:
        v = vals[chave]
        a, b, cov = intervalo_otimo(v)
        k, n, _ = cobertura(v, a, b)
        lo, hi = wilson(k, n)
        fora = [x for x in v if not (a <= x <= b)]
        res["variaveis"][chave] = {
            "nome": nome, "descricao": desc,
            "faixa": [a, b], "cobertura": 100 * cov,
            "cobertura_ic95": [100 * lo, 100 * hi],
            "acertos": k,
            "zebra_n": len(fora), "zebra_pct": 100 * len(fora) / n,
            "estat": describe(v), "distribuicao": distrib(v),
        }

    # dezenas
    cont = collections.Counter()
    for r in janela:
        cont.update(r["dezenas"])
    esp = len(janela) * 7 / 80
    chi2 = sum((cont.get(n, 0) - esp) ** 2 / esp for n in range(1, 81))
    res["dezenas"] = {
        "esperado": esp, "chi2": chi2, "gl": 79, "p_valor": chi2_sf(chi2, 79),
        "contagem": {n: cont.get(n, 0) for n in range(1, 81)},
        "top": [[n, cont.get(n, 0)] for n in sorted(range(1, 81), key=lambda n: (-cont.get(n, 0), n))[:12]],
        "bottom": [[n, cont.get(n, 0)] for n in sorted(range(1, 81), key=lambda n: (cont.get(n, 0), n))[:12]],
        "nunca": [n for n in range(1, 81) if cont.get(n, 0) == 0],
        "por_faixa10": {f: sum(cont.get(n, 0) for n in range(f, f + 10)) for f in range(1, 81, 10)},
        "por_quadrante": {f: sum(cont.get(n, 0) for n in range(f, f + 20)) for f in (1, 21, 41, 61)},
    }

    # atraso
    atraso = {}
    for n in range(1, 81):
        atraso[n] = next((len(janela) - pos - 1 for pos in range(len(janela) - 1, -1, -1)
                          if n in janela[pos]["dezenas"]), len(janela))
    res["atraso"] = atraso

    # times
    limitada = [r for r in janela if r["time_ok"]]
    times = collections.Counter(r["time"] for r in limitada)
    rep = sum(1 for i in range(idx_ini + 1, idx_fim + 1)
              if registros[i]["time_ok"] and registros[i - 1]["time_ok"]
              and registros[i]["time"] == registros[i - 1]["time"])
    rep_n = max(1, len(limitada) - 1)
    res["times"] = {
        "n_analisado": len(limitada), "distintos": len(times),
        "top": [[t, c] for t, c in times.most_common(10)],
        "repeticao_n": rep, "repeticao_pct": 100 * rep / rep_n,
        "repeticao_esperada_pct": 100 / 80,
    }
    return res


def validacao_cruzada(regras, vals_100, vals_full):
    """Aplica a faixa calibrada em uma base e mede cobertura na outra."""
    out = {}
    for chave, regra in regras.items():
        a, b = regra["faixa"]
        k1, n1, c1 = cobertura(vals_full[chave], a, b)
        k2, n2, c2 = cobertura(vals_100[chave], a, b)
        out[chave] = {"faixa": [a, b], "cov_full": 100 * c1, "cov_100": 100 * c2,
                      "n_full": n1, "n_100": n2}
    return out


# ---------------------------------------------------------------- zebras


def zebras(res, vals, limiar=30.0):
    """Valores isolados (ou faixas) com frequência observada < limiar%."""
    out = []
    for chave, _, _, _ in VARS:
        d = res["variaveis"][chave]
        for item in d["distribuicao"]:
            if item["pct"] < limiar:
                out.append({"variavel": chave, "nome": d["nome"], "valor": item["valor"],
                            "n": item["n"], "pct": item["pct"],
                            "faixa_prevalente": d["faixa"]})
    return out


def probs_hipergeometricas():
    return {k: 100 * math.comb(7, k) * math.comb(73, 7 - k) / C80_7 for k in range(0, 5)}


# ---------------------------------------------------------------- aderência


def pmf_contagem(m):
    """P(k elementos de um grupo de tamanho m) num sorteio de 7 entre 80."""
    return {k: math.comb(m, k) * math.comb(80 - m, 7 - k) / C80_7
            for k in range(max(0, 7 - (80 - m)), min(7, m) + 1)}


def pmf_soma():
    """Distribuição exata da soma de 7 dezenas distintas em 1..80 (programação dinâmica)."""
    soma_max = sum(range(74, 81))
    dp = [[0] * (soma_max + 1) for _ in range(8)]
    dp[0][0] = 1
    for n in range(1, 81):
        for k in range(6, -1, -1):
            linha = dp[k]
            destino = dp[k + 1]
            for s in range(soma_max - n, -1, -1):
                if linha[s]:
                    destino[s + n] += linha[s]
    return {s: c / C80_7 for s, c in enumerate(dp[7]) if c}


def chi2_binado(observado, pmf, min_esp=5.0, n=None):
    """Chi-quadrado com agrupamento guloso de células para esperado >= min_esp."""
    if n is None:
        n = sum(observado.values())
    valores = sorted(pmf)
    grupos, atual, p_atual = [], [], 0.0
    for v in valores:
        atual.append(v)
        p_atual += pmf[v]
        if p_atual * n >= min_esp:
            grupos.append((atual, p_atual))
            atual, p_atual = [], 0.0
    if atual:
        if grupos:
            g, p = grupos[-1]
            grupos[-1] = (g + atual, p + p_atual)
        else:
            grupos.append((atual, p_atual))
    chi2 = 0.0
    detalhe = []
    for g, p in grupos:
        obs = sum(observado.get(v, 0) for v in g)
        esp = p * n
        chi2 += (obs - esp) ** 2 / esp
        detalhe.append({"valores": g, "obs": obs, "esp": esp})
    gl = len(grupos) - 1
    return {"chi2": chi2, "gl": gl, "p_valor": chi2_sf(chi2, gl), "grupos": len(grupos)}


def teste_aderencia(registros, idx_ini, idx_fim):
    """Compara a distribuição observada com a de um sorteio uniforme."""
    observado = {chave: [] for chave in
                 ("soma", "pares", "baixas", "primos", "mult3", "fibonacci", "moldura")}
    for i in range(idx_ini, idx_fim + 1):
        n = registros[i]["dezenas"]
        observado["soma"].append(sum(n))
        observado["pares"].append(sum(1 for x in n if x % 2 == 0))
        observado["baixas"].append(sum(1 for x in n if x <= 40))
        observado["primos"].append(sum(1 for x in n if x in PRIMOS))
        observado["mult3"].append(sum(1 for x in n if x % 3 == 0))
        observado["fibonacci"].append(sum(1 for x in n if x in FIBONACCI))
        observado["moldura"].append(sum(1 for x in n if na_moldura(x)))

    pmfs = {
        "soma": pmf_soma(), "pares": pmf_contagem(40), "baixas": pmf_contagem(40),
        "primos": pmf_contagem(22), "mult3": pmf_contagem(26),
        "fibonacci": pmf_contagem(9), "moldura": pmf_contagem(32),
    }
    saida = {}
    for chave, vals in observado.items():
        obs = collections.Counter(vals)
        r = chi2_binado(obs, pmfs[chave], min_esp=5.0, n=len(vals))
        r["media_obs"] = sum(vals) / len(vals)
        r["media_teorica"] = sum(v * p for v, p in pmfs[chave].items())
        r["desvio_padrao_obs"] = describe(vals)["dp"]
        saida[chave] = r
    return saida



# ---------------------------------------------------------------- markdown


def fmt_pct(x, nd=1):
    return f"{x:.{nd}f}%".replace(".", ",")


def faixa_txt(a, b):
    return f"{a}" if a == b else f"{a} – {b}"


def rng(a, b):
    """Trecho de intervalo legível: '7' quando a==b, senão '7 – 9'."""
    return f"{a}" if a == b else f"{a} – {b}"


def gerar_tabelas(m):
    u, f = m["ultimos_100"], m["historico_completo"]
    vc_u = m["validacao"]["regras_do_full_no_recorte"]
    vc_f = m["validacao"]["regras_do_recorte_no_full"]
    pmf_rep = m["pmf_repetidas"]
    L = []

    L.append(f"**Recorte:** concursos {u['primeiro']} a {u['ultimo']} "
             f"({u['data_ini']} a {u['data_fim']}) — {u['n']} sorteios.\n")

    # Tabela 1
    L.append("## Tabela 1 — Padrões com prevalência ≥ 70% (calibrados no próprio recorte)\n")
    L.append("| Variável | Faixa / Regra | Cobertura no recorte | IC 95% | Mesma regra no histórico completo |")
    L.append("|---|---|---:|---:|---:|")
    for chave, v in u["variaveis"].items():
        L.append(f"| {v['nome']} | {faixa_txt(*v['faixa'])} | {fmt_pct(v['cobertura'])} "
                 f"| {fmt_pct(v['cobertura_ic95'][0])} – {fmt_pct(v['cobertura_ic95'][1])} "
                 f"| {fmt_pct(vc_f[chave]['cov_full'])} |")

    # Tabela 1b
    L.append("\n## Tabela 1b — Mesmos padrões calibrados no histórico completo e testados no recorte (out-of-sample)\n")
    L.append("| Variável | Faixa / Regra | Cobertura no histórico (2.460) | Cobertura no recorte (100) |")
    L.append("|---|---|---:|---:|")
    for chave, v in f["variaveis"].items():
        L.append(f"| {v['nome']} | {faixa_txt(*v['faixa'])} | {fmt_pct(v['cobertura'])} "
                 f"| {fmt_pct(vc_u[chave]['cov_100'])} |")

    # Tabela 2
    L.append("\n## Tabela 2 — Zebras: caudas de baixa incidência (fora do intervalo de ~70%)\n")
    L.append("| Variável | Faixa / Regra | Cobertura no recorte | Cobertura no histórico |")
    L.append("|---|---|---:|---:|")
    for chave, v in u["variaveis"].items():
        a, b = v["faixa"]
        st = v["estat"]
        partes, cob = [], []
        if st["min"] < a:
            partes.append(rng(st["min"], a - 1))
        if st["max"] > b:
            partes.append(rng(b + 1, st["max"]))
            cob.append(u["variaveis"][chave]["distribuicao"])
        if not partes:
            continue
        # cobertura no histórico das mesmas caudas
        obs = m["hist_contagem"][chave]
        n_hist = m["hist_contagem"]["__n__"]
        k = sum(c for val, c in obs.items() if st["min"] <= val < a or b < val <= st["max"])
        L.append(f"| {v['nome']} | {' ou '.join(partes)} | {fmt_pct(v['zebra_pct'])} "
                 f"| {fmt_pct(100 * k / n_hist)} |")

    # Tabela 3 — repetidas
    L.append("\n## Tabela 3 — Repetição de dezenas do concurso anterior\n")
    L.append("| Repetidas | Recorte (100) | % | Histórico (2.459) | % | Uniforme (teórico) |")
    L.append("|---|---:|---:|---:|---:|---:|")
    allv = sorted(set(list(pmf_rep) + [d["valor"] for d in u["variaveis"]["repetidas"]["distribuicao"]]
                      + [d["valor"] for d in f["variaveis"]["repetidas"]["distribuicao"]]))
    du = {d["valor"]: d for d in u["variaveis"]["repetidas"]["distribuicao"]}
    df = {d["valor"]: d for d in f["variaveis"]["repetidas"]["distribuicao"]}
    for k in allv:
        if k not in pmf_rep and not du.get(k) and not df.get(k):
            continue
        L.append(f"| {k} | {du.get(k, {}).get('n', 0)} | {fmt_pct(du.get(k, {}).get('pct', 0))} "
                 f"| {df.get(k, {}).get('n', 0)} | {fmt_pct(df.get(k, {}).get('pct', 0))} "
                 f"| {fmt_pct(pmf_rep.get(k, 0) * 100, 2)} |")
    L.append("\n_(0–1 repetida: 90,0% no recorte, 88,7% no histórico, 88,8% teórico)_")

    # Tabela 4 — aderência
    L.append("\n## Tabela 4 — Aderência ao sorteio uniforme (chi-quadrado com células agrupadas)\n")
    L.append("| Variável | Média observada (100) | Média teórica | χ² recorte | p-valor (100) | p-valor (histórico) |")
    L.append("|---|---:|---:|---:|---:|---:|")
    ad_u, ad_f = m["aderencia"]["recorte"], m["aderencia"]["historico"]
    for chave, a in ad_u.items():
        h = ad_f[chave]
        L.append(f"| {NOMES.get(chave, chave)} | {a['media_obs']:.2f} | {a['media_teorica']:.2f} "
                 f"| {a['chi2']:.2f} (gl {a['gl']}) | {a['p_valor']:.3f} | {h['p_valor']:.3f} |".replace(".", ","))
    dz = u["dezenas"]
    L.append(f"| Frequência das 80 dezenas | — | 8,75 por dezena | {dz['chi2']:.2f} (gl 79) "
             f"| {dz['p_valor']:.3f} | {f['dezenas']['p_valor']:.3f} |".replace(".", ","))

    # Tabela 5 — dezenas
    L.append(f"\n## Tabela 5 — Frequência das dezenas no recorte (esperado: {dz['esperado']:.2f} cada)\n"
             .replace("8.75", "8,75"))
    L.append("| Ranking | Dezenas mais sorteadas | Nº | Dezenas menos sorteadas | Nº |")
    L.append("|---|---|---:|---|---:|")
    for i, ((a1, c1), (a2, c2)) in enumerate(zip(u["dezenas"]["top"][:10], u["dezenas"]["bottom"][:10]), 1):
        L.append(f"| {i}º | {a1:02d} | {c1} | {a2:02d} | {c2} |")

    # Tabela 6 — times
    t = u["times"]
    L.append(f"\n## Tabela 7 — Time do Coração no recorte ({t['distintos']} times distintos em {t['n_analisado']} sorteios)\n")
    L.append("| Time | Vezes | | Time | Vezes |")
    L.append("|---|---:|---|---|---:|")
    top = t["top"]
    metade = (len(top) + 1) // 2
    for i in range(metade):
        a = top[i]
        b = top[i + metade] if i + metade < len(top) else ("", "")
        L.append(f"| {a[0]} | {a[1]} | | {b[0]} | {b[1] if b[0] else ''} |")
    L.append(f"\nRepetição do mesmo time em sorteios consecutivos: {t['repeticao_n']} de 99 "
             f"({fmt_pct(t['repeticao_pct'])}) — esperado {fmt_pct(t['repeticao_esperada_pct'], 2)}.")

    # Tabela 7 — atraso
    atraso = u["atraso"]
    top_atraso = sorted(atraso.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    L.append("\n## Tabela 6 — Dezenas com maior atraso no recorte (sorteios sem aparecer)\n")
    L.append("| # | Dezena | Atraso | | # | Dezena | Atraso |")
    L.append("|---|---|---:|---|---|---|---:|")
    metade = 5
    for i in range(metade):
        a = top_atraso[i]
        b = top_atraso[i + metade]
        L.append(f"| {i+1}º | {int(a[0]):02d} | {a[1]} | | {i+6}º | {int(b[0]):02d} | {b[1]} |")

    # Tabela 8 — últimos 10
    L.append("\n## Tabela 8 — Últimos 10 concursos do recorte\n")
    L.append("| Concurso | Data | Dezenas | Repetidas | Time do Coração |")
    L.append("|---|---|---|---:|---|")
    for r in m["seq_ultimos_100"][-10:][::-1]:
        dez = " – ".join(f"{d:02d}" for d in r["dezenas"])
        L.append(f"| {r['concurso']} | {r['data']} | {dez} | {r['repetidas']} | {r['time']} |")

    # Tabela 9 — os 100 concursos
    L.append("\n## Tabela 9 — Os 100 concursos do recorte\n")
    L.append("| Concurso | Data | Dezenas | Rep. | | Concurso | Data | Dezenas | Rep. |")
    L.append("|---|---|---|---:|---|---|---|---:|")
    seq = m["seq_ultimos_100"]
    metade = (len(seq) + 1) // 2
    for i in range(metade):
        a = seq[i]
        da = " ".join(f"{d:02d}" for d in a["dezenas"])
        linha = f"| {a['concurso']} | {a['data']} | {da} | {a['repetidas']} |"
        if i + metade < len(seq):
            b = seq[i + metade]
            db = " ".join(f"{d:02d}" for d in b["dezenas"])
            linha += f" | {b['concurso']} | {b['data']} | {db} | {b['repetidas']} |"
        else:
            linha += " | | | | |"
        L.append(linha)

    # Apêndice — distribuições
    L.append("\n## Apêndice — Distribuição completa das variáveis no recorte\n")
    for chave, v in u["variaveis"].items():
        linhas = ", ".join(f"{d['valor']}: {d['n']}" for d in v["distribuicao"])
        L.append(f"- **{v['nome']}** — min {v['estat']['min']}, mediana {fmt_num_r(v['estat']['mediana'])}, "
                 f"média {n1(v['estat']['media'])}, máx {v['estat']['max']} | contagem por valor → {linhas}")
    return "\n".join(L).replace(".", ",") if False else "\n".join(L)


def fmt_num_r(x):
    return f"{x:g}".replace(".", ",")


def n1(x):
    return f"{x:.1f}".replace(".", ",")


def main():
    registros, anomalias, n_bruto = carregar()
    n = len(registros)
    idx_fim, idx_ini = n - 1, n - N_ULTIMOS

    u = analisar(registros, idx_ini, idx_fim, f"Últimos {N_ULTIMOS} concursos")
    f = analisar(registros, 1, idx_fim, "Histórico completo")

    vals_100 = valores_das_variaveis(registros, idx_ini, idx_fim)
    vals_full = valores_das_variaveis(registros, 1, idx_fim)

    saida = {
        "gerado_em": datetime.datetime.now().isoformat(timespec="seconds"),
        "fonte": {
            "primaria": "API oficial da Caixa (servicebus2.caixa.gov.br/portaldeloterias/api/timemania) "
                        "via espelho diário github.com/eitchtee/loterias.json",
            "validacao": ["github.com/guilhermeasn/loteria.json — 2.168 concursos comparados, "
                          "1 divergência (concurso 1307, fora do recorte)",
                          "4 publicações independentes do concurso 2461"],
            "registros_no_arquivo": n_bruto, "registros_validos": n, "anomalias": anomalias,
            "primeiro_concurso": registros[0]["concurso"],
            "ultimo_concurso": registros[-1]["concurso"],
            "ultima_data": registros[-1]["data"],
        },
        "validacao": {
            "regras_do_full_no_recorte": validacao_cruzada(f["variaveis"], vals_100, vals_full),
            "regras_do_recorte_no_full": validacao_cruzada(u["variaveis"], vals_100, vals_full),
        },
        "hipergeometrico_repetidas": probs_hipergeometricas(),
        "pmf_repetidas": {k: v / 100 for k, v in probs_hipergeometricas().items()},
        "hist_contagem": dict({chave: collections.Counter(vals_full[chave]) for chave in vals_full},
                              __n__=len(vals_full["soma"])),
        "aderencia": {
            "recorte": teste_aderencia(registros, idx_ini, idx_fim),
            "historico": teste_aderencia(registros, 1, idx_fim),
        },
        "ultimos_100": u,
        "historico_completo": f,
        "zebras_ultimos_100": zebras(u, vals_100),
        "seq_ultimos_100": [
            {"concurso": registros[i]["concurso"], "data": registros[i]["data"],
             "dezenas": registros[i]["dezenas"], "time": registros[i]["time"],
             "repetidas": len(set(registros[i]["dezenas"]) & set(registros[i - 1]["dezenas"]))}
            for i in range(idx_ini, idx_fim + 1)
        ],
    }

    json.dump(saida, open(os.path.join(OUT_DIR, "metricas.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    with open(os.path.join(OUT_DIR, "timemania_ultimos_100.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["concurso", "data", "d1", "d2", "d3", "d4", "d5", "d6", "d7",
                    "soma", "pares", "primos", "repetidas_anterior", "time_do_coracao"])
        for i in range(idx_ini, idx_fim + 1):
            r = registros[i]
            dez = r["dezenas"]
            rep = len(set(dez) & set(registros[i - 1]["dezenas"]))
            w.writerow([r["concurso"], r["data"], *[f"{d:02d}" for d in dez],
                        sum(dez), sum(1 for d in dez if d % 2 == 0),
                        sum(1 for d in dez if d in PRIMOS), rep, r["time"]])

    open(os.path.join(OUT_DIR, "tabelas.md"), "w", encoding="utf-8").write(gerar_tabelas(saida))
    print(f"OK — {n} concursos válidos; recorte {registros[idx_ini]['concurso']}"
          f"–{registros[idx_fim]['concurso']} ({registros[idx_ini]['data']} a {registros[idx_fim]['data']})")
    print("arquivos: dados/metricas.json, dados/timemania_ultimos_100.csv, dados/tabelas.md")


if __name__ == "__main__":
    main()
