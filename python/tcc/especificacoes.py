"""
tcc.especificacoes — Variáveis alternativas e catálogo de modelos (Tabelas 5 a 8 e Apêndice C do TCC)
=====================================================================================================

Cada modelo do catálogo responde a uma pergunta econômica definida antes de olhar o
valor de p; nenhum é escolhido pelo resultado (MacKinnon, Nielsen e Webb, 2023).
Só o modelo principal recebe o ajuste de Holm; as sensibilidades são exploratórias.

| Grupo de modelos             | Pergunta                                                     | Tabela do TCC        |
|------------------------------|--------------------------------------------------------------|----------------------|
| principal                    | Associação dos três fundamentos com o valor                  | 5, 6, 7; Ap. C 4     |
| sem_winsor                   | A winsorização criou o sinal?                                | 7                    |
| excluir_<empresa>            | Uma empresa sozinha determina o resultado?                   | 7, Figura 1, Ap. C 1 |
| sem_EKTR_TAEE, grupos        | Vínculos societários afetam a inferência?                    | 7; Ap. C 3           |
| balanceado                   | O painel não balanceado distorce o resultado?                | 7; Ap. C 2           |
| cotacoes_desde_dia20         | Preços de ações pouco negociadas afetam o resultado?         | 7                    |
| historico(_mesmas_empresas)  | O resultado se mantém em 2012–2025?                          | 7                    |
| controle_PL, ROA, níveis     | A medida de rentabilidade muda a conclusão? (Ohlson, 1995)   | 7, 8                 |
| divida_ampla                 | Omitir aplicações financeiras (1.01.02) explica o sinal?     | 7, 8                 |
| sem_CEB_*, sem_transicoes    | Eventos societários (CEB, Auren, Light) explicam o sinal?    | 7; Ap. C 2           |
| contemporaneo, ROE_media3,   | Alinhamento temporal e suavização da rentabilidade           | Ap. C 3              |
| ROE_PLmedio, defasado_*      |                                                              |                      |
| somente_consolidadas         | Misturar consolidado e individual (Elektro) importa?         | Ap. C 3              |
"""
import json                                                 # diagnósticos em JSON
import numpy as np                                          # cálculos
import pandas as pd                                         # tabelas
from . import config as C                                   # parâmetros
from .entradas import aplicacoes_financeiras               # conta 1.01.02
from .estimacao import estimar, holm, vif_intra, fracao_fwl, matriz_efeitos_fixos  # estimação e diagnósticos
from .painel import winsorizar                              # percentis 1 e 99

V = C.FUNDAMENTOS                                           # atalho: ROE, AL e PORTE defasados


def painel_completo(d: pd.DataFrame, fin: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:  # painel principal + variáveis alternativas
    """Acrescenta ao painel principal todas as variáveis das especificações alternativas."""
    # Medidas alternativas de rentabilidade e patrimônio, do exercício t−1 (Tabela 8)
    alt = fin[["ticker", "ano"]].copy()                       # chave empresa-exercício
    alt["lnpl_lag"] = np.log(fin.pl_controladora.where(fin.pl_controladora > 0))   # ln(PL da controladora)
    alt["roa_lag"] = fin["3.11"] / fin["1"]                 # ROA líquido = lucro total / ativo (mesmo escopo)
    alt["roa_oper_lag"] = fin["3.05"] / fin["1"]            # ROA operacional = EBIT / ativo
    alt["pl_bi_lag"] = fin.pl_controladora / 1e9            # modelo em níveis: PL em R$ bilhões
    alt["ll_bi_lag"] = fin.lucro_controladora / 1e9         # e lucro em R$ bilhões (preserva prejuízos)
    alt["ano"] += 1                                         # defasagem de um ano
    d = d.merge(alt, on=["ticker", "ano"], validate="one_to_one")  # junta as medidas de t−1
    d["mcap_bi"] = d.mcap / 1e9                             # capitalização em R$ bilhões (modelo em níveis)
    for v in ["roa_lag", "roa_oper_lag"]:                   # ROAs também winsorizados (TCC, mesma seção)
        d[v + "_bruto"] = d[v]                                # guarda o valor original
        d[v] = winsorizar(d[v])                               # percentis 1 e 99 na amostra válida

    # Dívida ampliada: subtrai também as aplicações financeiras (1.01.02); 1.01.01 já inclui equivalentes (CPC, 2010)
    f2 = fin.merge(aplicacoes_financeiras(), on=["CD_CVM", "ano", "escopo"], how="left", validate="one_to_one")  # acrescenta a conta 1.01.02
    f2["dl_ampla_lag"] = (f2["2.01.04"] + f2["2.02.01"] - f2["1.01.01"] - f2.aplicacoes) / f2.ebitda.where(f2.ebitda > 0)  # AL ampliada = (DCP + DLP − CX − aplicações) / EBITDA
    f2["ano"] += 1                                          # defasagem
    d = d.merge(f2[["ticker", "ano", "dl_ampla_lag", "aplicacoes"]], on=["ticker", "ano"], validate="one_to_one")  # junta a dívida ampliada de t−1
    d["dl_ampla_lag_bruto"] = d.dl_ampla_lag                  # valor original (média 2,2793)
    d["dl_ampla_lag"] = winsorizar(d.dl_ampla_lag)            # winsorizada

    # ROE médio dos três exercícios anteriores consecutivos (mesmo escopo) e ROE com PL médio
    fo = fin.sort_values(["ticker", "ano"])                 # exercícios em ordem
    media3, plmedio = [], []                                  # listas de resultados
    for r in d.itertuples():                                # cada observação do painel
        q = fo[fo.ticker.eq(r.ticker) & fo.ano.isin([r.ano - 3, r.ano - 2, r.ano - 1])]   # t−3, t−2, t−1
        ok = (len(q) == 3 and q.roe.notna().all()           # três ROEs disponíveis
              and q.escopo.nunique() == 1 and q.escopo.iloc[-1] == r.escopo_lag)          # escopo constante
        media3.append(q.roe.mean() if ok else np.nan)         # média aritmética dos três ROEs
        t1 = fo[fo.ticker.eq(r.ticker) & fo.ano.eq(r.ano - 1)]     # exercício t−1 (PL final)
        t2 = fo[fo.ticker.eq(r.ticker) & fo.ano.eq(r.ano - 2)]     # exercício t−2 (PL inicial)
        ok = (len(t1) == len(t2) == 1 and t1.escopo.iloc[0] == t2.escopo.iloc[0]  # dois exercícios no mesmo escopo
              and t1.pl_controladora.iloc[0] > 0 and t2.pl_controladora.iloc[0] > 0)       # saldos positivos
        plmedio.append(t1.lucro_controladora.iloc[0] / ((t1.pl_controladora.iloc[0] + t2.pl_controladora.iloc[0]) / 2)  # LL(t−1) / média do PL inicial e final
                       if ok else np.nan)                     # ausente se não houver os dois saldos
    d["roe_media3"], d["roe_plmedio"] = media3, plmedio       # novas colunas (74 e 75 válidas)
    for v in ["roe_media3", "roe_plmedio"]:                 # winsorização na amostra válida de cada medida
        d[v + "_bruto"] = d[v]                                # guarda o valor original
        d[v] = winsorizar(d[v])                               # percentis 1 e 99 na amostra válida

    d["grupo"] = d.ticker.replace(C.GRUPOS_SOCIETARIOS)     # 12 grupos de inferência
    datas = comp.groupby(["ticker", "ano"]).data.min().reset_index()     # negócio mais antigo entre as classes
    d = d.merge(datas, on=["ticker", "ano"], validate="one_to_one")  # data do negócio
    d["dia_cotacao"] = d.data.astype(str).str[-2:].astype(int)           # dia do último negócio usado
    return d                                                  # painel completo


def painel_contemporaneo(d: pd.DataFrame, fin: pd.DataFrame) -> pd.DataFrame:  # fundamentos do mesmo ano
    """Fundamentos do MESMO ano da capitalização (versão retrospectiva: a DFP sai depois de dezembro)."""
    atual = fin[["ticker", "ano", "roe", "dl", "size", "pl_controladora", "ebitda"]].rename(  # fundamentos do exercício t
        columns={"roe": "roe_atual", "dl": "dl_atual", "size": "size_atual",  # (renomeia)
                 "pl_controladora": "pl_atual", "ebitda": "ebitda_atual"})  # (renomeia)
    c = d.merge(atual, on=["ticker", "ano"], validate="one_to_one")     # mesmas linhas do painel principal
    c = c[c.pl_atual.gt(0) & c.ebitda_atual.gt(0)].dropna(subset=["roe_atual", "dl_atual", "size_atual"])  # PL e EBITDA positivos e fundamentos válidos (73 linhas)
    for v in ["roe_atual", "dl_atual"]:                     # winsorização na própria amostra (73 linhas)
        c[v] = winsorizar(c[v])                               # limites da própria amostra
    return c                                                  # painel contemporâneo


def catalogo(d: pd.DataFrame, h: pd.DataFrame, cont: pd.DataFrame) -> list:  # lista de modelos
    """Lista (nome, dados, variáveis, dependente, grupo). A ordem define a ordem das saídas."""
    sem_winsor = d.copy()                                     # cópia para desfazer a winsorização
    for v in V[:2]:                                           # ROE e AL
        sem_winsor[v] = sem_winsor[v + "_bruto"]            # ROE e AL sem winsorização
    n_emp = d.groupby("ticker").size()                      # anos por empresa
    ceb = d.ticker.eq("CEBR3")                              # linhas da CEB
    transicoes = pd.Series(False, index=d.index)            # janelas de eventos societários
    for tk, anos in C.TRANSICOES.items():                     # CEB, Auren e Light
        transicoes |= d.ticker.eq(tk) & d.ano.isin(anos)      # marca as linhas da janela
    VROA = ["roa_lag", "dl_lag", "size_lag"]                  # ROA no lugar do ROE
    m = lambda nome, dados, vars_=V, dep="ln_mcap", grp="ticker": (nome, dados, vars_, dep, grp)  # atalho para montar uma especificação
    return [                                                  # catálogo na ordem das saídas
        m("principal", d),                                  # Tabelas 5 e 6
        m("sem_winsor", sem_winsor),                        # Tabela 7
        *[m(f"excluir_{e}", d[d.ticker != e]) for e in sorted(d.ticker.unique())],   # Figura 1; Ap. C 1
        m("sem_EKTR_TAEE", d[~d.ticker.isin(["EKTR3", "TAEE3"])]),  # sem as empresas com vínculo societário (Tabela 7)
        m("balanceado", d[d.ticker.isin(n_emp[n_emp == 6].index)]),     # só empresas com os seis anos
        m("cotacoes_desde_dia20", d[d.dia_cotacao >= C.DIA_MINIMO_COTACAO]),  # filtro de liquidez: 73 linhas
        m("historico", h),                                  # 2012–2025
        m("historico_mesmas_empresas", h[h.ticker.isin(d.ticker.unique())]),  # histórico só com as 14 do principal: 89 linhas
        m("controle_PL", d, V + ["lnpl_lag"]),              # Tabela 8: + ln(PL)
        m("ROA", d, VROA),                                  # Tabela 8: ROA líquido
        m("ROA_operacional", d, ["roa_oper_lag", "dl_lag", "size_lag"]),  # Tabela 8: EBIT/ativo
        m("lucro_PL_niveis", d, ["ll_bi_lag", "pl_bi_lag"], "mcap_bi"),  # em níveis, inspirado em Ohlson (1995)
        m("divida_ampla", d, ["roe_lag", "dl_ampla_lag", "size_lag"]),  # Tabela 8: AL ampliada
        m("sem_CEB_2022", d[~(ceb & d.ano.eq(2022))]),      # Ap. C 2
        m("sem_CEB_2021_2022", d[~(ceb & d.ano.isin([2021, 2022]))]),  # mercado de 2021–2022 da CEB
        m("sem_transicoes", d[~transicoes]),                # 69 linhas (Light 2023 já ausente)
        m("contemporaneo", cont, ["roe_atual", "dl_atual", "size_atual"]),   # Ap. C 3
        m("defasado_amostra_contemporanea", cont),          # principal nas mesmas 73 linhas
        m("ROE_media3", d, ["roe_media3", "dl_lag", "size_lag"]),  # Ap. C 3: média de três anos
        m("defasado_amostra_media3", d[d.roe_media3.notna()]),          # mesmas 74 linhas
        m("ROE_PLmedio", d, ["roe_plmedio", "dl_lag", "size_lag"]),  # Ap. C 3: PL médio
        m("defasado_amostra_PLmedio", d[d.roe_plmedio.notna()]),        # mesmas 75 linhas
        m("grupos_societarios", d, grp="grupo"),            # 12 grupos, 4.096 combinações
        m("somente_consolidadas", d[d.escopo_lag.eq("con")]),           # sem as 4 linhas individuais da Elektro
        # Diagnósticos adicionais do pacote (não tabelados no texto do TCC)
        m("sem_CEB_2020_2022", d[~(ceb & d.ano.between(2020, 2022))]),  # diagnóstico extra
        *[m(f"sem_CEB_{a}", d[~(ceb & d.ano.eq(a))]) for a in (2020, 2021, 2023, 2024, 2025)],  # retirada de um ano da CEB por vez
        m("ROA_sem_CEB", d[~ceb], VROA),                      # diagnóstico extra
    ]                                                         # fim do catálogo


def estimar_todos(d, h, fin, comp, saida):                    # roda o catálogo e grava as saídas
    """Estima o catálogo, aplica Holm e grava modelos, coeficientes e diagnósticos em `saida`."""
    d = painel_completo(d, fin, comp)                       # variáveis alternativas
    d.to_csv(saida / "painel_completo.csv", index=False)      # grava o painel com todas as variáveis
    cont = painel_contemporaneo(d, fin)                       # 73 linhas
    modelos, coefs, base = [], [], None                       # acumuladores
    for nome, dados, vars_, dep, grp in catalogo(d, h, cont):  # 44 modelos
        mod, cf, extras = estimar(dados, nome, vars_, dep, grp)          # CR1, WCR e DK
        modelos.append(mod)                                   # guarda o resumo
        coefs += cf                                           # guarda os coeficientes
        if nome == "principal":                               # o principal alimenta os diagnósticos
            base = extras                                   # guarda para os diagnósticos
        print(f"  {nome:32s} N={mod['N']:3d} G={mod['G']:2d} K={mod['K']:2d}", flush=True)  # acompanhamento no console
    modelos, coefs = pd.DataFrame(modelos), pd.DataFrame(coefs)  # tabelas
    modelos.to_csv(saida / "modelos.csv", index=False)        # N, G, K e R² de cada modelo
    coefs.to_csv(saida / "coeficientes.csv", index=False)     # coeficientes, CR1, WCR e DK

    # Holm (1979) só para as três hipóteses do modelo principal (H1, H2, H3)
    pr = coefs[coefs.modelo.eq("principal")].set_index("variavel")  # três hipóteses do modelo principal
    hl = pr[["coef", "p_WCR"]].copy()                         # base do ajuste
    hl["p_Holm"] = holm(pr.p_WCR)                           # 0,0077 ; 0,0259 ; 0,0122
    hl.reset_index().to_csv(saida / "holm.csv", index=False)  # grava holm.csv

    # VIF e correlações intra (modelo principal e modelo com ln(PL))
    X, F = base["X"], base["F"]                               # matrizes do principal
    vif, corr = vif_intra(F, X[:, base["pos"]])               # 1,02 ; 1,36 ; 1,35
    vif_pl, _ = vif_intra(matriz_efeitos_fixos(d), d[V + ["lnpl_lag"]].to_numpy(float))  # com ln(PL)
    (saida / "diagnosticos.json").write_text(json.dumps(dict(  # grava os diagnósticos
        VIF_intra=dict(zip(V, vif)), correlacao_intra=corr.tolist(),  # (continuação)
        VIF_intra_controle_PL=dict(zip(V + ["lnpl_lag"], vif_pl)),  # (continuação)
        aplicacoes_ausentes=int(d.aplicacoes.isna().sum())), indent=2))  # nenhuma das 76 linhas sem a conta 1.01.02

    # Concentração da informação (FWL) e influência de cada observação no modelo principal
    a, e, P = base["dados"], base["e"], base["P"]             # dados, resíduos e pseudo-inversa
    alav = np.sum(X * P.T, axis=1)                          # h_ii: alavancagem estatística da observação
    inf = a[["ticker", "ano", "roe_lag", "roe_lag_bruto"]].copy()  # identificação das observações
    inf["residuo"], inf["alavancagem_hat"] = e, alav          # resíduo e alavancagem estatística
    for v, j in zip(V, base["pos"]):                          # cada fundamento
        inf["fracao_variacao_" + v] = fracao_fwl(X, j)      # de onde vem a informação de β_j
        inf["delta_exclusao_" + v] = -P[j, :] * e / (1 - alav)          # mudança de β_j ao retirar a linha
    inf.to_csv(saida / "influencia_observacoes.csv", index=False)  # grava por observação
    inf.groupby("ticker")[[c for c in inf if c.startswith("fracao_")]].sum().to_csv(saida / "variacao_por_empresa.csv")  # soma por empresa (CEB = 54,55% no ROE)
    return modelos, coefs                                     # resumos e coeficientes
