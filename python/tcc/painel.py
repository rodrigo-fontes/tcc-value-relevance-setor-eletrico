"""
tcc.painel — Defasagem, elegibilidade e painéis (TCC, seções "Seleção da amostra" e "Fundamentos contábeis e defasagem")
=====================================================================================================================

Regras, na ordem em que são aplicadas:
    1. Defasagem: a capitalização de dezembro de t é ligada aos fundamentos do exercício t−1
       (dezembro de 2020 aos indicadores de 2019). As DFPs anuais são divulgadas depois de
       dezembro; o modelo pergunta pelos fundamentos já conhecidos.
    2. Elegibilidade: capitalização conciliada (status "ok") e os três fundamentos válidos.
       Valores ausentes não são preenchidos.
    3. Cobertura: pelo menos quatro exercícios por empresa. Com efeitos fixos de empresa, só a
       variação dentro da empresa identifica os coeficientes (Wooldridge, 2019; Hsiao, 2022).
    4. Ano com uma só empresa é excluído (2010–2011 no painel histórico: só a EDP).
    5. Winsorização de ROE e alavancagem nos percentis 1 e 99 de cada painel: valores fora dos
       limites são substituídos pelos limites, preservando as linhas. Porte e capitalização não
       recebem esse tratamento. Os valores originais ficam em *_bruto.

Resultado (Tabela 1 e funil do TCC): 138 combinações → 90 com capitalização conciliada →
84 com os três fundamentos → 76 observações de 14 empresas (2020–2025). Painel histórico:
97 observações de 15 empresas (2012–2025).
"""
import numpy as np                                          # logaritmo
import pandas as pd                                         # tabelas
from . import config as C                                   # anos, mínimos e percentis


def winsorizar(s: pd.Series) -> pd.Series:                    # percentis 1 e 99
    """Limita a série aos percentis 1 e 99 da própria amostra (quantil com interpolação linear;
    Hyndman e Fan, 1996, tipo 7, igual ao padrão do R)."""
    lo, hi = s.quantile(list(C.PERCENTIS_WINSOR))           # limites inferior e superior (ignora ausentes)
    return s.clip(lo, hi)                                   # substitui os extremos pelos limites


def decisoes(cap: pd.DataFrame, fin: pd.DataFrame) -> pd.DataFrame:  # empresa-ano com fundamentos de t−1
    """Junta capitalização (ano t) e fundamentos (exercício t−1) em uma linha por empresa-ano."""
    lag = fin[["ticker", "ano", "roe", "dl", "size", "escopo"]].copy()    # fundamentos de cada exercício
    lag["ano"] += 1                                         # exercício t−1 passa a valer para o mercado de t
    lag = lag.rename(columns={c: c + "_lag" for c in ["roe", "dl", "size", "escopo"]})   # sufixo _lag
    dec = cap.merge(lag, on=["ticker", "ano"], how="left", validate="one_to_one")       # mantém todas as linhas
    dec["ln_mcap"] = np.log(dec.mcap)                       # eq. (2): y = ln(VM)
    dec["elegivel_contabil"] = dec[C.FUNDAMENTOS].notna().all(axis=1)    # os três fundamentos existem
    return dec                                                # todas as empresas-ano, incluídas ou não


def montar(dec: pd.DataFrame, rotulo: str) -> pd.DataFrame:   # painel principal ou histórico
    """Aplica as regras 2 a 5 a um período: 'principal' (2020–2025) ou 'historico' (2010–2025)."""
    inicio = C.ANO_INICIO_PRINCIPAL if rotulo == "principal" else C.ANO_INICIO_HISTORICO  # 2020 ou 2010
    z = dec[dec.ano.ge(inicio) & dec.status.eq("ok") & dec.elegivel_contabil].copy()   # regra 2
    n_emp = z.groupby("ticker").size()                      # exercícios por empresa
    z = z[z.ticker.isin(n_emp[n_emp >= C.MIN_EXERCICIOS].index)]            # regra 3
    n_ano = z.groupby("ano").size()                         # empresas por ano
    z = z[z.ano.isin(n_ano[n_ano >= C.MIN_EMPRESAS_ANO].index)]             # regra 4
    z = z.sort_values(["ticker", "ano"]).reset_index(drop=True)            # ordem estável
    for v in C.FUNDAMENTOS[:2]:                             # regra 5: ROE e alavancagem
        z[v + "_bruto"] = z[v]                              # guarda o valor original
        z[v] = winsorizar(z[v])                             # limites calculados neste painel
    return z                                                  # painel final


def funil(dec: pd.DataFrame) -> dict:                         # contagens do funil
    """Contagens do funil da amostra principal (23 emissoras × 6 anos)."""
    j = dec[dec.ano.between(C.ANO_INICIO_PRINCIPAL, C.ANO_FIM)]           # 2020–2025
    return dict(combinacoes=len(j),                         # 138
                capitalizacao_conciliada=int(j.status.eq("ok").sum()),     # 90
                tres_fundamentos_validos=int((j.status.eq("ok") & j.elegivel_contabil).sum()),   # 84
                minimo_quatro_anos=int(j.incluido_principal.sum()))        # 76
