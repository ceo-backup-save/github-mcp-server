#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fechamento matemático da Timemania — quantitativo de apostas por matriz v-10-7-7.

Regras do jogo consideradas (premissas fixas, ver filtros-timemania.json):
  * universo de 80 dezenas, 7 sorteadas por concurso;
  * aposta SEMPRE de 10 dezenas (não existe volante ampliado), R$ 3,50;
  * o Time do Coração é ignorado — este estudo é só das 7 dezenas.

Para cada universo de v dezenas calcula:
  * apostas possíveis sem filtro .......... C(v,10)
  * apostas possíveis com filtros ......... contagem exata por programação dinâmica
  * mínimo teórico para garantir 7 acertos  limite de Schönheim e limite de contagem
  * quantas apostas novas cada etapa acrescenta ao fechamento anterior
  * custo e probabilidade resultantes

Uso: python3 scripts/fechamento.py
"""

import itertools
import json
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREMISSAS = os.path.join(BASE, "filtros-timemania.json")
METRICAS = os.path.join(BASE, "dados", "metricas.json")
OUT = os.path.join(BASE, "dados", "fechamento.json")

V_UNIVERSO = [20, 30, 40, 50, 60, 70, 80]
DEZENAS_POR_APOSTA = 10
SORTEADAS = 7
PRECO = 3.50


# --------------------------------------------------------------- quantitativos


def comb(n, k):
    return math.comb(n, k) if 0 <= k <= n else 0


def schoenheim(v, k, t):
    """Limite inferior de Schönheim para o número de blocos de uma cobertura C(v,k,t)."""
    memo = {}

    def s(vv, kk, tt):
        if tt == 0:
            return 1
        if (vv, kk, tt) in memo:
            return memo[(vv, kk, tt)]
        if tt == 1:
            r = math.ceil(vv / kk)
        else:
            r = math.ceil(vv / kk * s(vv - 1, kk - 1, tt - 1))
        memo[(vv, kk, tt)] = r
        return r

    return s(v, k, t)


def minimo_teorico(v):
    """Menor nº de apostas que pode cobrir todos os C(v,7) resultados com 7 dezenas em v."""
    contagem = math.ceil(comb(v, SORTEADAS) / comb(DEZENAS_POR_APOSTA, SORTEADAS))
    return {"contagem": contagem, "schoenheim": schoenheim(v, DEZENAS_POR_APOSTA, SORTEADAS)}


# --------------------------------------------------------- contagem com filtros


def contar_apostas(dezenas, anteriores, pares=(0, 10), faixas=(1, 8), bloco_max=10):
    """Nº exato de apostas de 10 dezenas (subconjuntos de `dezenas`) que passam nos filtros.

    Programação dinâmica sobre as dezenas 1..80, com estado
      (k = dezenas escolhidas, run = sequência consecutiva corrente,
       ov = dezenas da aposta presentes no sorteio anterior,
       par = pares escolhidos, mask = faixas de 10 já ocupadas)
    """
    permitidas = set(dezenas)
    anteriores = set(anteriores)
    pmin, pmax = pares
    fmin, fmax = faixas

    # estado -> contagem
    dp = {(0, 0, 0, 0, 0): 1}
    for d in range(1, 81):
        membro = d in permitidas
        novo = {}
        faixa_bit = 1 << ((d - 1) // 10)
        e_par = 1 if d % 2 == 0 else 0
        no_anterior = 1 if d in anteriores else 0
        for (k, run, ov, par, mask), c in dp.items():
            # não escolher a dezena: a sequência consecutiva zera
            chave = (k, 0, ov, par, mask)
            novo[chave] = novo.get(chave, 0) + c
            if not membro or k == DEZENAS_POR_APOSTA:
                continue
            if run + 1 > bloco_max:
                continue
            npar = par + e_par
            if npar > pmax:
                continue
            nov = ov + no_anterior
            if nov > 1:                      # filtro de repetição: no máximo 1
                continue
            nmask = mask | faixa_bit
            chave = (k + 1, run + 1, nov, npar, nmask)
            novo[chave] = novo.get(chave, 0) + c
        dp = novo

    total = 0
    for (k, run, ov, par, mask), c in dp.items():
        if k != DEZENAS_POR_APOSTA or par < pmin:
            continue
        if not (fmin <= bin(mask).count("1") <= fmax):
            continue
        total += c
    return total


def contar_bruto(dezenas):
    return comb(len(dezenas), DEZENAS_POR_APOSTA)


# ------------------------------------------------------------------- relatório


def main():
    prem = json.load(open(PREMISSAS, encoding="utf-8"))
    met = json.load(open(METRICAS, encoding="utf-8"))
    fa = prem["filtros_aposta_10"]
    pares = tuple(fa["pares_entre"])
    faixas = tuple(fa["faixas_ocupadas_entre"])
    bloco_max = fa["maior_bloco_consecutivo_max"]

    cont = met["historico_completo"]["dezenas"]["contagem"]
    ordem = sorted(range(1, 81), key=lambda n: (-cont[str(n)], n))
    anterior = prem["sorteio_anterior"]["dezenas"]

    linhas = []
    anterior_n = None
    for v in V_UNIVERSO:
        universo = ordem[:v]
        bruto = contar_bruto(universo)
        filtrado = contar_apostas(universo, anterior, pares, faixas, bloco_max)
        minimo = minimo_teorico(v)
        # quantas apostas novas em relação à etapa anterior (conjuntos aninhados)
        novos = bruto - (anterior_n["sem_filtro"] if anterior_n else 0)
        novos_f = filtrado - (anterior_n["com_filtro"] if anterior_n else 0)
        linha = {
            "v": v,
            "dezenas_no_anterior": len(set(universo) & set(anterior)),
            "sem_filtro": bruto,
            "com_filtro": filtrado,
            "reducao_pct": 100 * (1 - filtrado / bruto),
            "novas_sem_filtro": novos,
            "novas_com_filtro": novos_f,
            "minimo_contagem": minimo["contagem"],
            "minimo_schoenheim": minimo["schoenheim"],
            "cobertura_por_aposta": comb(DEZENAS_POR_APOSTA, SORTEADAS),  # 120
            "p_v_universo": comb(v, SORTEADAS) / comb(80, SORTEADAS),
            "custo_sem_filtro": bruto * PRECO,
            "custo_com_filtro": filtrado * PRECO,
            "custo_minimo": minimo["schoenheim"] * PRECO,
        }
        linhas.append(linha)
        anterior_n = linha

    # funil de filtros para o universo de 20 dezenas (cada filtro isolado e acumulado)
    u20 = ordem[:20]
    funil = [
        {"rotulo": "sem filtro", "apostas": contar_apostas(u20, [], (0, 10), (1, 8), 10)},
        {"rotulo": "F1 repetição ≤ 1", "apostas": contar_apostas(u20, anterior, (0, 10), (1, 8), 10)},
        {"rotulo": "F1 + F2 pares 4–6", "apostas": contar_apostas(u20, anterior, pares, (1, 8), 10)},
        {"rotulo": "F1 + F2 + F3 faixas 4–6",
         "apostas": contar_apostas(u20, anterior, pares, faixas, 10)},
        {"rotulo": "F1 + F2 + F3 + F4 bloco ≤ 2",
         "apostas": contar_apostas(u20, anterior, pares, faixas, bloco_max)},
    ]

    # prob. de um resultado passar em cada filtro de sorteio (7 dezenas)
    probs = {
        "repetidas_0_1_pct": 100 * (math.comb(7, 0) * math.comb(73, 7) + math.comb(7, 1) * math.comb(73, 6))
        / math.comb(80, 7),
        "pares_3_4_pct": 100 * (math.comb(40, 3) * math.comb(40, 4) + math.comb(40, 4) * math.comb(40, 3))
        / math.comb(80, 7),
    }

    saida = {
        "premissas": prem,
        "universo_dezenas": ordem,
        "anterior": anterior,
        "tabela": linhas,
        "funil_20": funil,
        "probabilidades_sorteio": probs,
        "preco_aposta": PRECO,
    }
    json.dump(saida, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    cab = f"{'v':>3} {'sem filtro':>18} {'com filtro':>16} {'redução':>8} {'mín. Schönheim':>15}"
    print(cab)
    for ln in linhas:
        print(f"{ln['v']:>3} {ln['sem_filtro']:>18,} {ln['com_filtro']:>16,} "
              f"{ln['reducao_pct']:>7.1f}% {ln['minimo_schoenheim']:>15,}".replace(",", "."))
    print("\nfunil 20 dezenas:")
    for f in funil:
        print(f"  {f['rotulo']:<32} {f['apostas']:>10,}".replace(",", "."))
    print(f"\narquivo: {OUT}")


if __name__ == "__main__":
    main()
