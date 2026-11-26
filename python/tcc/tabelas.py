"""
tcc.tabelas — Tabelas e Figura 1 no formato do TCC
==================================================

Gera em `resultados/tabelas_tcc/` um CSV por tabela do trabalho, com o mesmo
arredondamento do texto (ponto decimal no CSV; o relatório em PDF converte
para vírgula). "*" marca p WCR < 0,05 ANTES do arredondamento.

| Arquivo                                   | No TCC                                             |
|-------------------------------------------|----------------------------------------------------|
| tabela_1_cobertura.csv                    | Tabela 1. Cobertura anual dos painéis              |
| tabela_2_etapas.csv                       | Tabela 2. Etapas (+ módulo que executa cada uma)   |
| tabela_3_variaveis.csv                    | Tabela 3. Definição e unidade das variáveis        |
| tabela_4_descritivas.csv                 | Tabela 4. Estatísticas descritivas                 |
| tabela_5_coeficientes.csv                 | Tabela 5. Coeficientes e inferência agrupada       |
| tabela_6_cr1_wcr_holm.csv                 | Tabela 6. p CR1 e WCR (+ Holm, citado no texto)    |
| interpretacao_efeitos.csv                 | Texto: −6,16%, −9,62% e +5,04% (eq. 8)             |
| tabela_7_sensibilidade.csv (+ contagem)   | Tabela 7. Matriz de sensibilidade (18 linhas)      |
| tabela_8_especificacoes.csv               | Tabela 8. Especificações alternativas              |
| apA_tabela_1_companhias.csv               | Apêndice A, Tabela 1 (N recalculado do painel)     |
| apA_tabela_2_fora_do_painel.csv           | Apêndice A, Tabela 2 (contagens + restrição)       |
| apB_tabela_1_rubricas.csv                 | Apêndice B, Tabela 1. Rubricas contábeis           |
| apC_tabela_1..4                           | Apêndice C, Tabelas 1 a 4                          |
| diagnosticos_texto.json                   | R², VIF, concentração da CEB, dívida ampliada      |
| figura_1.png                              | Figura 1. Retirada de cada empresa                 |
"""
import json                                                 # JSON
import numpy as np                                          # exp
import pandas as pd                                         # tabelas
import matplotlib                                           # gráficos
matplotlib.use("Agg")                                       # sem janela (gera arquivo)
import matplotlib.pyplot as plt                               # interface de desenho
from . import config as C                                     # parâmetros e nomes

NOMES_FUND = {"roe_lag": "ROE defasado", "dl_lag": "Alavancagem defasada", "size_lag": "Porte defasado"}  # rótulos dos fundamentos nas tabelas
# Linhas da Tabela 7, na ordem do TCC: (rótulo, modelo)
LINHAS_T7 = [("Principal", "principal"), ("Sem winsorização", "sem_winsor"), ("Sem CEB", "excluir_CEBR3"),  # 18 linhas da Tabela 7, na ordem do texto
             ("Sem Auren", "excluir_AURE3"), ("Sem Light", "excluir_LIGT3"), ("Sem Taesa", "excluir_TAEE3"),  # (continuação)
             ("Sem Elektro e Taesa", "sem_EKTR_TAEE"), ("Balanceado", "balanceado"),  # (continuação)
             ("Negócios desde 20 dez.", "cotacoes_desde_dia20"), ("Histórico", "historico"),  # (continuação)
             ("Histórico: mesmas 14", "historico_mesmas_empresas"), ("+ ln(PL)", "controle_PL"),  # (continuação)
             ("ROA líquido", "ROA"), ("ROA operacional", "ROA_operacional"), ("Dívida ampliada", "divida_ampla"),  # (continuação)
             ("Sem CEB-2022", "sem_CEB_2022"), ("CEB: sem 2021–22", "sem_CEB_2021_2022"),  # (continuação)
             ("Sem transições", "sem_transicoes")]            # (fim)
ROTULOS_T8 = {"roe_lag": "ROE", "dl_lag": "Alavancagem", "size_lag": "ln(ativo)", "lnpl_lag": "ln(PL)",  # rótulos das variáveis da Tabela 8
              "roa_lag": "ROA líquido", "roa_oper_lag": "ROA operacional", "ll_bi_lag": "Lucro (R$ bi)",  # (continuação)
              "pl_bi_lag": "PL (R$ bi)", "dl_ampla_lag": "Alav. ampliada"}  # (fim)


def f(x, n=4):                                                # formata com n casas
    """Número com n casas decimais (vazio se ausente)."""
    return "" if pd.isna(x) else f"{x:.{n}f}"                 # vazio se ausente


def fp(p):                                                    # formata valor de p
    """Valor de p no formato do texto do TCC: '< 0.0001' quando menor que 0,0001."""
    return "< 0.0001" if p < 0.0001 else f(p)                 # regra do texto do TCC


def gerar(saida):                                             # gera todas as tabelas
    """Gera todas as tabelas e a Figura 1 a partir dos resultados em `saida`."""
    tab = saida / "tabelas_tcc"                               # pasta de saída
    tab.mkdir(exist_ok=True)                                  # cria se não existir
    coef = pd.read_csv(saida / "coeficientes.csv")            # coeficientes de todos os modelos
    mod = pd.read_csv(saida / "modelos.csv").set_index("modelo")  # resumo dos modelos
    d = pd.read_csv(saida / "painel_principal.csv")           # 76 observações
    h = pd.read_csv(saida / "painel_historico.csv")           # 97 observações
    Cf = coef.set_index(["modelo", "variavel"])             # acesso por (modelo, variável)
    V = C.FUNDAMENTOS                                         # ROE, AL e PORTE
    ngk = lambda m: f"{int(mod.loc[m, 'N'])}/{int(mod.loc[m, 'G'])}/{int(mod.loc[m, 'K'])}"   # "76/14/22"

    # Tabela 1 — empresas por ano em cada painel
    anos = range(2010, 2026)                                  # anos de mercado coletados
    t1 = pd.DataFrame(dict(ano=[str(a) for a in anos], principal=[int((d.ano == a).sum()) for a in anos],  # contagem por ano
                           historico=[int((h.ano == a).sum()) for a in anos]))  # (continuação)
    t1 = t1[(t1.principal > 0) | (t1.historico > 0)].reset_index(drop=True)  # só anos com alguma empresa
    t1.loc[len(t1)] = ["total", len(d), len(h)]             # 76 e 97
    t1.loc[len(t1)] = ["empresas", d.ticker.nunique(), h.ticker.nunique()]   # 14 e 15
    t1.to_csv(tab / "tabela_1_cobertura.csv", index=False)    # grava a Tabela 1

    # Tabela 4 — descritivas (ROE em %, capitalização em R$ bilhões); desvio-padrão amostral (n−1)
    desc = {"Valor de mercado (R$ bilhões)": d.mcap / 1e9, "ln do valor de mercado": d.ln_mcap,  # as cinco variáveis da Tabela 4
            "ROE defasado (%)": d.roe_lag * 100, "Alavancagem defasada (vezes)": d.dl_lag,  # (continuação)
            "Porte defasado (ln R$)": d.size_lag}             # (fim)
    pd.DataFrame([dict(variavel=k, media=f(v.mean(), 2), desvio_padrao=f(v.std(), 2), minimo=f(v.min(), 2),  # média, desvio, mínimo, mediana e máximo
                       mediana=f(v.median(), 2), maximo=f(v.max(), 2)) for k, v in desc.items()]  # (continuação)
                 ).to_csv(tab / "tabela_4_descritivas.csv", index=False)  # grava a Tabela 4

    # Tabela 5 — coeficientes, erro-padrão CR1, p com t(13) e intervalo de 95%
    pd.DataFrame([dict(fundamento=NOMES_FUND[v], coeficiente=f(Cf.loc[("principal", v), "coef"]),  # uma linha por fundamento
                       erro_padrao=f(Cf.loc[("principal", v), "se_CR1"]), p_CR1=fp(Cf.loc[("principal", v), "p_CR1"]),  # (continuação)
                       IC95_inf=f(Cf.loc[("principal", v), "IC_inf"]), IC95_sup=f(Cf.loc[("principal", v), "IC_sup"]))  # (continuação)
                  for v in V]).to_csv(tab / "tabela_5_coeficientes.csv", index=False)  # grava a Tabela 5

    # Tabela 6 — CR1 × WCR, com o ajuste de Holm citado no texto e as contagens exatas do bootstrap
    hl = pd.read_csv(saida / "holm.csv").set_index("variavel")  # p de Holm
    pd.DataFrame([dict(fundamento=NOMES_FUND[v], p_CR1=fp(Cf.loc[("principal", v), "p_CR1"]),  # CR1, WCR e Holm
                       p_WCR=f(Cf.loc[("principal", v), "p_WCR"]), p_Holm=f(hl.loc[v, "p_Holm"]),  # (continuação)
                       excedencias=int(Cf.loc[("principal", v), "excedencias"]),  # (continuação)
                       combinacoes=int(Cf.loc[("principal", v), "combinacoes"])) for v in V]  # (continuação)
                 ).to_csv(tab / "tabela_6_cr1_wcr_holm.csv", index=False)  # grava a Tabela 6

    # Eq. (8): Δ%VM = 100 [exp(β Δx) − 1]; para o porte (log-log), 1,10^β − 1
    b = {v: Cf.loc[("principal", v), "coef"] for v in V}      # β1, β2, β3
    pd.DataFrame([                                            # três linhas
        dict(fundamento="ROE +10 p.p.", calculo="exp(b x 0,10) - 1", efeito_pct=f(100 * (np.exp(b["roe_lag"] * .10) - 1), 2)),  # Δx = 0,10 → −6,16%
        dict(fundamento="Alavancagem +1 vez", calculo="exp(b) - 1", efeito_pct=f(100 * (np.exp(b["dl_lag"]) - 1), 2)),  # Δx = 1 → −9,62%
        dict(fundamento="Ativo +10%", calculo="1,10^b - 1", efeito_pct=f(100 * (1.10 ** b["size_lag"] - 1), 2))]  # elasticidade → +5,04%
    ).to_csv(tab / "interpretacao_efeitos.csv", index=False)  # grava

    # Tabela 7 — p WCR das 18 verificações, com "*" se p < 0,05 antes do arredondamento
    def estrela(m, v):                                        # p WCR com asterisco
        p = Cf.loc[(m, v), "p_WCR"]                           # valor exato
        return f(p) + ("*" if p < C.NIVEL else "")            # "*" se p < 0,05 antes de arredondar
    t7 = []                                                   # linhas da Tabela 7
    for rot, m in LINHAS_T7:                                  # 18 verificações
        vs = coef[coef.modelo.eq(m)].variavel.tolist()      # variáveis do modelo
        rent = [v for v in vs if v.startswith(("roe", "roa"))][0]       # ROE, ou ROA nas linhas de ROA
        alav = [v for v in vs if v.startswith("dl")][0]     # AL, ou AL ampliada
        t7.append(dict(modelo=rot, N_G_K=ngk(m), R2_intra=f(mod.loc[m, "R2_intra"], 3),  # N/G/K, R² intra e três p WCR
                       rentabilidade=estrela(m, rent), alavancagem=estrela(m, alav), porte=estrela(m, "size_lag")))  # (continuação)
    t7 = pd.DataFrame(t7)                                     # tabela
    t7.to_csv(tab / "tabela_7_sensibilidade.csv", index=False)  # grava a Tabela 7
    cont = {c: int(t7[c].str.endswith("*").sum()) for c in ["rentabilidade", "alavancagem", "porte"]}   # 12, 13, 15
    (tab / "tabela_7_contagem.json").write_text(json.dumps(dict(linhas=len(t7), significativos=cont), indent=2,  # contagens 12/13/15
                                                           ensure_ascii=False))  # (fim)

    # Tabela 8 — especificações alternativas na mesma amostra
    t8 = []                                                   # linhas da Tabela 8
    for rot, m in [("+ ln(PL)", "controle_PL"), ("ROA líquido", "ROA"), ("ROA operacional", "ROA_operacional"),  # cinco especificações
                   ("Lucro e PL", "lucro_PL_niveis"), ("Dívida ampliada", "divida_ampla")]:  # (continuação)
        for r in coef[coef.modelo.eq(m)].itertuples():        # cada variável do modelo
            t8.append(dict(modelo=rot, variavel=ROTULOS_T8[r.variavel], coef=f(r.coef), p_CR1=fp(r.p_CR1),  # coeficiente, p CR1 e p WCR
                           p_WCR=f(r.p_WCR), N_G_K=ngk(m), R2_intra=f(mod.loc[m, "R2_intra"], 3)))  # (continuação)
    pd.DataFrame(t8).to_csv(tab / "tabela_8_especificacoes.csv", index=False)  # grava a Tabela 8

    # Apêndice C, Tabela 1 — retirada de cada empresa: coeficiente (erro-padrão CR1)
    pd.DataFrame([dict(retirada=e, N_G_K=ngk("excluir_" + e), R2_intra=f(mod.loc["excluir_" + e, "R2_intra"], 3),  # Apêndice C, Tabela 1
                       **{NOMES_FUND[v].split()[0]: f"{Cf.loc[('excluir_' + e, v), 'coef']:.3f} "  # "coef (erro-padrão)" para cada fundamento
                                                   f"({Cf.loc[('excluir_' + e, v), 'se_CR1']:.3f})" for v in V})  # (continuação)
                  for e in sorted(d.ticker.unique())]).to_csv(tab / "apC_tabela_1_retiradas.csv", index=False)  # 14 retiradas; grava

    # Apêndice C, Tabela 2 — painel balanceado e janelas de transição (com DK1)
    c2 = []                                                   # linhas do Apêndice C, Tabela 2
    for rot, m in [("Balanceado", "balanceado"), ("Sem CEB em 2022", "sem_CEB_2022"),  # quatro recortes
                   ("CEB: sem 2021–22", "sem_CEB_2021_2022"), ("Sem transições", "sem_transicoes")]:  # (continuação)
        for v in V:                                           # cada fundamento
            r = Cf.loc[(m, v)]                                # linha do coeficiente
            c2.append(dict(modelo=rot, variavel=NOMES_FUND[v], coef=f(r.coef), p_CR1=fp(r.p_CR1), p_WCR=f(r.p_WCR),  # coeficiente e quatro p
                           p_DK1=fp(r.p_DK1), N_G_K=ngk(m), R2_intra=f(mod.loc[m, "R2_intra"], 3)))  # (continuação)
    pd.DataFrame(c2).to_csv(tab / "apC_tabela_2_balanceado_janelas.csv", index=False)  # grava

    # Apêndice C, Tabela 3 — alinhamento temporal, rentabilidade e agrupamento
    c3 = []                                                   # linhas do Apêndice C, Tabela 3
    for rot, m in [("Contemporâneo", "contemporaneo"), ("Defasado: mesmas 73", "defasado_amostra_contemporanea"),  # oito modelos
                   ("ROE médio: três anos", "ROE_media3"), ("Defasado: mesmas 74", "defasado_amostra_media3"),  # (continuação)
                   ("ROE: PL médio", "ROE_PLmedio"), ("Defasado: mesmas 75", "defasado_amostra_PLmedio"),  # (continuação)
                   ("Grupos societários", "grupos_societarios"), ("Só consolidadas", "somente_consolidadas")]:  # (continuação)
        for r in coef[coef.modelo.eq(m)].itertuples():        # cada variável do modelo
            c3.append(dict(modelo=rot, variavel=r.variavel, coef=f(r.coef), p_CR1=fp(r.p_CR1), p_WCR=f(r.p_WCR),  # coeficiente, p CR1 e p WCR
                           N_G_K=ngk(m), R2_intra=f(mod.loc[m, "R2_intra"], 3)))  # (continuação)
    pd.DataFrame(c3).to_csv(tab / "apC_tabela_3_alinhamento_agrupamento.csv", index=False)  # grava

    # Apêndice C, Tabela 4 — Driscoll–Kraay do modelo principal
    pd.DataFrame([dict(fundamento=NOMES_FUND[v], p_DK1=fp(Cf.loc[("principal", v), "p_DK1"]),  # Apêndice C, Tabela 4
                       p_DK2=fp(Cf.loc[("principal", v), "p_DK2"])) for v in V]  # (continuação)
                 ).to_csv(tab / "apC_tabela_4_driscoll_kraay.csv", index=False)  # grava

    # Tabelas descritivas (texto e códigos) e as do Apêndice A
    tabelas_descritivas(saida)                                # Tabelas 2 e 3, Apêndice A (1 e 2), Apêndice B (1)

    # Números citados no texto do TCC
    dg = json.loads((saida / "diagnosticos.json").read_text())  # VIF
    inf = pd.read_csv(saida / "influencia_observacoes.csv")   # frações por observação
    var = pd.read_csv(saida / "variacao_por_empresa.csv").set_index("ticker")  # frações por empresa
    pc = pd.read_csv(saida / "painel_completo.csv")           # painel com dívida ampliada
    resumo = dict(                                            # números citados no texto
        R2_global=f(mod.loc["principal", "R2_global"]), R2_intra=f(mod.loc["principal", "R2_intra"]),  # 0,9711 ; 0,2130
        R2_parcial=f(mod.loc["principal", "R2_parcial"]),     # 0,2896
        VIF_intra={NOMES_FUND[k]: f(v, 2) for k, v in dg["VIF_intra"].items()},  # 1,02 ; 1,36 ; 1,35
        CEB_fracao_variacao_ROE_pct=f(100 * var.loc["CEBR3", "fracao_variacao_roe_lag"], 2),  # 54,55%
        CEB_2022_fracao_variacao_ROE_pct=f(100 * inf[(inf.ticker == "CEBR3") & (inf.ano == 2022)].fracao_variacao_roe_lag.iloc[0], 2),  # 31,38%
        divida_media_bruta=f(pc.dl_lag_bruto.mean()), divida_ampliada_media_bruta=f(pc.dl_ampla_lag_bruto.mean()),  # 2,5057 → 2,2793
        funil=json.loads((saida / "funil.json").read_text()))  # 138 → 90 → 84 → 76
    (tab / "diagnosticos_texto.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False))  # grava

    fig = plt.figure(figsize=(6.3, 4.6))                    # Figura 1 avulsa (PNG)
    axs = [fig.add_subplot(1, 3, k + 1) for k in range(3)]    # três painéis
    desenhar_figura1(axs, coef, d)                            # desenha
    fig.tight_layout(w_pad=1)                                 # ajusta margens
    fig.savefig(saida / "figura_1.png", dpi=300)              # grava o PNG
    plt.close(fig)                                            # libera memória
    return t7, cont                                           # Tabela 7 e contagens


def elegibilidade(saida):                                     # empresa × janela principal
    """Por empresa, na janela do painel principal (2020–2025): anos com capitalização conciliada,
    anos com os três fundamentos de t−1, exercícios elegíveis (os dois ao mesmo tempo), anos no
    painel e os motivos de exclusão registrados (do mais ao menos frequente). É a base das duas tabelas do Apêndice A."""
    d = pd.read_csv(saida / "decisoes_amostra.csv")           # uma linha por empresa-ano (todas as 23 emissoras)
    d = d[d.ano.between(C.ANO_INICIO_PRINCIPAL, C.ANO_FIM)].copy()  # janela 2020–2025
    d["capitalizacao_ok"] = d.status.eq("ok")                 # capitalização conciliada
    d["fundamentos_ok"] = d[C.FUNDAMENTOS].notna().all(axis=1)  # ROE, AL e PORTE de t−1 disponíveis
    d["elegivel"] = d.capitalizacao_ok & d.fundamentos_ok      # entra antes do mínimo de quatro anos
    motivo = lambda s: ";".join(s[s.ne("ok")].value_counts().index)  # códigos de exclusão, do mais ao menos frequente
    return d.groupby("ticker").agg(anos=("ano", "size"), capitalizacao=("capitalizacao_ok", "sum"),  # contagens por empresa
                                   fundamentos=("fundamentos_ok", "sum"), elegiveis=("elegivel", "sum"),  # (continuação)
                                   no_painel=("incluido_principal", "sum"), motivo=("status", motivo))  # (fim)


# Tradução dos códigos de exclusão gravados por tcc.capitalizacao
MOTIVOS = {"excluir_preco_classe_ausente": "sem cotação de dezembro da classe",  # P da mesma classe ausente
           "excluir_capital_ambiguo_ou_ausente": "capital ambíguo ou ausente na CVM",  # Q não determinada
           "excluir_tesouraria_nao_documentada": "tesouraria não documentada",  # T ausente
           "excluir_subclasses_ou_tesouraria": "subclasses (PNA/PNB) ou tesouraria sem repartição",  # Q por classe indeterminada
           "excluir_divergencia_tesouraria_DFP_FRE": "tesouraria divergente entre DFP e FRE",  # T inconsistente
           "excluir_divergencia_tesouraria_FRE": "tesouraria ambígua no FRE",  # T inconsistente
           "excluir_tesouraria_evento_posterior": "evento societário com tesouraria",  # evento desfeito + T
           "excluir_quantidade_invalida": "quantidade em circulação não positiva"}  # Q − T ≤ 0


def tabelas_descritivas(saida):                               # tabelas sem estimação
    """Tabelas 2 e 3 do TCC, Apêndice A (Tabelas 1 e 2) e Apêndice B (Tabela 1).
    O texto vem de config (o mesmo do TCC); os números e as listas de empresas vêm dos dados."""
    tab = saida / "tabelas_tcc"                               # pasta de saída
    pd.DataFrame(C.ETAPAS_TCC, columns=["etapa", "procedimento", "modulo"]  # Tabela 2 + módulo que executa
                 ).assign(modulo=lambda t: "tcc." + t.modulo).to_csv(tab / "tabela_2_etapas.csv", index=False)  # grava
    pd.DataFrame(C.VARIAVEIS_TCC, columns=["medida", "definicao", "unidade", "equacao", "coluna"]  # Tabela 3
                 ).to_csv(tab / "tabela_3_variaveis.csv", index=False)  # grava

    el = elegibilidade(saida)                                 # contagens por empresa (2020–2025)
    d = pd.read_csv(saida / "painel_principal.csv")           # 76 observações
    car = pd.read_csv(C.DADOS / "documentos" / "caracterizacao_empresas.csv")  # segmento e relação societária (TCC)
    a1 = car.rename(columns={"codigo": "ticker", "segmento_G_geracao_T_transmissao_D_distribuicao": "segmento"})  # nomes curtos
    a1["N"] = a1.ticker.map(d.groupby("ticker").size())       # N recalculado a partir do painel (não o digitado)
    a1[["companhia", "ticker", "N", "segmento", "relacao_societaria"]].to_csv(  # colunas do Apêndice A, Tabela 1
        tab / "apA_tabela_1_companhias.csv", index=False)     # grava

    fora = el[el.no_painel.eq(0)].reset_index()               # emissoras sem nenhum ano no painel principal
    fora["motivos_no_codigo"] = fora.motivo.map(lambda m: "; ".join(MOTIVOS[x] for x in m.split(";") if x))  # motivos legíveis
    tcc = pd.read_csv(C.DADOS / "documentos" / "companhias_fora_painel_tcc.csv")  # restrições como escritas no TCC
    fora = fora.merge(tcc, on="ticker", how="outer")          # outer: uma empresa só de um lado aparece
    fora[["identificador", "ticker", "capitalizacao", "fundamentos", "elegiveis", "motivos_no_codigo", "restricao_tcc"]  # colunas
         ].to_csv(tab / "apA_tabela_2_fora_do_painel.csv", index=False)  # grava

    pd.DataFrame(C.RUBRICAS, columns=["conta", "demonstracao", "codigo"]  # Apêndice B, Tabela 1
                 ).to_csv(tab / "apB_tabela_1_rubricas.csv", index=False)  # grava


def desenhar_figura1(axs, coef, d):                           # Figura 1
    """Figura 1 do TCC: coeficiente e intervalo CR1 de 95% após retirar cada empresa.
    Linha tracejada = modelo principal; losango = retirada da CEB."""
    Cf = coef.set_index(["modelo", "variavel"])               # acesso por modelo e variável
    emps = sorted(d.ticker.unique())                        # 14 empresas em ordem alfabética do código
    for k, (ax, v, tit) in enumerate(zip(axs, C.FUNDAMENTOS, ["A. ROE", "B. Alavancagem", "C. Porte"])):  # um painel por fundamento
        ax.axvline(0, color=".65", lw=.7)                   # referência: coeficiente zero
        ax.axvline(Cf.loc[("principal", v), "coef"], color=".35", ls="--", lw=1)   # modelo principal
        for i, e in enumerate(emps):                          # uma linha por empresa retirada
            r = Cf.loc[("excluir_" + e, v)]                 # modelo sem a empresa e
            ceb = e == "CEBR3"                                # destaque da CEB
            ax.errorbar(r.coef, i, xerr=[[r.coef - r.IC_inf], [r.IC_sup - r.coef]], fmt="D" if ceb else "o",  # ponto e intervalo CR1 de 95%
                        color="black" if ceb else ".45", markersize=4 if ceb else 2.6, lw=.9, capsize=1.5)  # (continuação)
        ax.set_ylim(len(emps) - .5, -.5)                    # primeira empresa no topo
        ax.set_yticks(range(len(emps)))                       # uma marca por empresa
        ax.set_yticklabels([C.NOMES_EMPRESAS[e] for e in emps] if k == 0 else [], fontsize=7.5)  # nomes só no primeiro painel
        ax.tick_params(axis="x", labelsize=7)                 # tamanho dos números
        ax.set_title(tit, fontsize=8.5, loc="left")           # A, B ou C
        ax.set_xlabel("Coeficiente e IC 95%", fontsize=7.5)   # rótulo do eixo
        ax.spines[["top", "right"]].set_visible(False)        # sem bordas superior e direita
