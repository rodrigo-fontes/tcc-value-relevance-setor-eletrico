"""
tcc.conferencia — Três conferências independentes dos resultados
================================================================

A. Pacote original    resultados/ × referencia/ (saídas do pacote Base_final_TCC, set/2026),
                      com tolerância relativa de 10⁻⁸ e contagens do bootstrap EXATAS.
B. Bibliotecas        coeficientes, CR1, R² e Driscoll–Kraay recalculados por statsmodels
                      (OLS com indicadoras) e linearmodels (PanelOLS), como declarado no TCC.
C. Texto do TCC       os 465 valores impressos no trabalho (dados/documentos/valores_publicados_tcc.csv)
                      recalculados e formatados com as mesmas casas decimais.

`executar()` devolve True se tudo coincidir.
"""
import json                                                 # JSON
import numpy as np                                          # comparações numéricas
import pandas as pd                                         # tabelas
from . import config as cfg                                 # (não "C": colidiria com C() das fórmulas do statsmodels)
from .valores import valor, formatar                        # mesma regra do relatório

TOL = 1e-8                                                  # tolerância relativa


class Registro:                                               # acumulador de resultados
    """Acumula e imprime o resultado de cada comparação."""

    def __init__(self):                                       # inicia sem falhas
        self.falhas = []                                    # rótulos que falharam

    def num(self, rotulo, a, b, tol=TOL):                     # comparação numérica
        """Compara arrays numéricos: diferença relativa máxima e mesmos ausentes."""
        a, b = np.asarray(a, float), np.asarray(b, float)     # converte para vetores
        dif = np.nanmax(np.abs(a - b) / np.maximum(1, np.abs(b))) if a.size else 0.0  # diferença relativa máxima
        ok = dif <= tol and np.array_equal(np.isnan(a), np.isnan(b))  # dentro da tolerância e mesmos ausentes
        print(f"  [{'ok' if ok else 'FALHA'}] {rotulo:60s} diferença máx. {dif:.1e}")  # linha do relatório
        if not ok:                                            # falhou
            self.falhas.append(rotulo)                        # registra

    def tabela(self, rotulo, a, b):                           # comparação de tabelas
        """Compara duas tabelas inteiras (numéricas com tolerância 10⁻¹⁰; texto exato)."""
        a, b = a.reset_index(drop=True), b.reset_index(drop=True)  # índices iguais
        ok = a.shape == b.shape and list(a.columns) == list(b.columns)  # mesmo formato e colunas
        for c in (a.columns if ok else []):                   # coluna a coluna
            if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):  # numérica?
                x, y = a[c].to_numpy(float), b[c].to_numpy(float)  # vetores
                ok &= np.array_equal(np.isnan(x), np.isnan(y)) and np.allclose(x[~np.isnan(x)], y[~np.isnan(y)], rtol=1e-10, atol=0)  # iguais até 10⁻¹⁰
            else:                                             # texto
                ok &= a[c].fillna("NA").astype(str).equals(b[c].fillna("NA").astype(str))  # texto idêntico
        print(f"  [{'ok' if ok else 'FALHA'}] {rotulo}")      # linha do relatório
        if not ok:                                            # falhou
            self.falhas.append(rotulo)                        # registra


def pacote_original(R: Registro, saida):                      # conferência A
    """A. Mesmos números do pacote que gerou o TCC."""
    print("A. Resultados × pacote original (referencia/)")    # título
    ref = cfg.REFERENCIA                                      # pasta de referência
    for r, p in [("capitalizacao_final", "capitalizacao"), ("componentes_final", "componentes_capitalizacao"),  # arquivos da construção
                 ("financeiro_final", "financeiro"), ("correcoes_lucro", "correcoes_lucro"),  # (continuação)
                 ("decisoes_amostra", "decisoes_amostra"), ("painel_principal", "painel_principal"),  # (continuação)
                 ("painel_historico", "painel_historico")]:   # (fim)
        R.tabela(f"{p}.csv idêntico ao original", pd.read_csv(ref / f"{r}.csv"), pd.read_csv(saida / f"{p}.csv"))  # tabela idêntica?
    coef = pd.read_csv(saida / "coeficientes.csv")            # coeficientes
    mod = pd.read_csv(saida / "modelos.csv").set_index("modelo")  # modelos
    integ = pd.read_csv(ref / "estimativas_integral.csv")   # 37 modelos com CR1 e WCR
    j = integ.merge(coef, on=["modelo", "variavel"], suffixes=("_ref", ""))  # pareia por modelo e variável
    assert len(j) == len(integ), "modelo da referência ausente no catálogo"  # todos os modelos de referência existem
    for c in ["coef", "se_CR1", "p_CR1", "IC_inf", "IC_sup", "p_WCR"]:  # cada estatística
        R.num(f"{c} ({j.modelo.nunique()} modelos, {len(j)} coeficientes)", j[c], j[c + "_ref"])  # compara
    R.num("excedências do WCR (contagens exatas)", j.excedencias, j.excedencias_ref, 0)  # contagens idênticas (tolerância zero)
    bo = pd.read_csv(ref / "bootstrap_revisao.csv").merge(coef, on=["modelo", "variavel"])  # WCR dos modelos só da revisão
    R.num(f"p WCR dos modelos da revisão ({bo.modelo.nunique()} modelos)", bo.p_WCR, bo.p_bootstrap)  # compara
    for arq in ["estimativas_revisao", "estimativas_finais"]:              # Driscoll–Kraay
        r = pd.read_csv(ref / f"{arq}.csv")                   # estimativas com DK
        for bw in cfg.DEFASAGENS_DK:                          # 1 e 2 defasagens
            x = r[r.metodo.eq(f"DK{bw}")].merge(coef, on=["modelo", "variavel"])  # linhas DK
            R.num(f"Driscoll–Kraay {bw}: erro-padrão ({arq})", x[f"se_DK{bw}"], x.se)  # compara
            R.num(f"Driscoll–Kraay {bw}: valor de p ({arq})", x[f"p_DK{bw}"], x.p)  # compara
    mi = pd.read_csv(ref / "modelos_integral.csv").set_index("modelo")  # N, G, K e R² de referência
    for c in ["N", "G", "K", "R2_intra", "R2_parcial"]:       # cada campo
        R.num(f"{c} ({len(mi)} modelos)", mod.loc[mi.index, c], mi[c])  # compara
    mf = pd.read_csv(ref / "modelos_finais.csv").set_index("modelo")  # R² global de referência
    comuns = mf.index.intersection(mod.index)                 # modelos em comum
    R.num(f"R² global ({len(comuns)} modelos)", mod.loc[comuns, "R2_global"], mf.loc[comuns, "r2_inclusive"])  # compara
    hr = pd.read_csv(ref / "holm_principal.csv").set_index("variavel")  # Holm de referência
    hp = pd.read_csv(saida / "holm.csv").set_index("variavel")  # Holm calculado
    R.num("p de Holm", hp.loc[hr.index, "p_Holm"], hr.p_Holm)  # compara
    dr = json.loads((ref / "diagnosticos.json").read_text())  # VIF de referência
    dp = json.loads((saida / "diagnosticos.json").read_text())  # VIF calculado
    R.num("VIF intra", list(dp["VIF_intra"].values()), list(dr["VIF_within"].values()))  # compara
    R.num("VIF intra com ln(PL)", list(dp["VIF_intra_controle_PL"].values()),  # compara
          list(json.loads((ref / "diagnosticos_revisao.json").read_text())["VIF_controle_PL"].values()))  # (continuação)
    vr = pd.read_csv(ref / "variacao_por_empresa.csv").set_index("ticker")  # FWL de referência
    vp = pd.read_csv(saida / "variacao_por_empresa.csv").set_index("ticker")  # FWL calculado
    R.num("fração FWL por empresa", vp.loc[vr.index, vr.columns], vr)  # compara
    ir, ip = pd.read_csv(ref / "influencia_observacoes.csv"), pd.read_csv(saida / "influencia_observacoes.csv")  # influência: referência e calculada
    cols = ["residuo", "alavancagem_hat"] + [c for c in ir if c.startswith(("fracao_", "delta_"))]  # colunas comparadas
    R.num("influência de cada observação", ip[cols], ir[cols])  # compara


def bibliotecas(R: Registro, saida):                          # conferência B
    """B. As fórmulas próprias coincidem com statsmodels e linearmodels."""
    print("\nB. Resultados × statsmodels e linearmodels")     # título
    import statsmodels.formula.api as smf                   # OLS com indicadoras (LSDV)
    from linearmodels.panel import PanelOLS                 # efeitos fixos de duas vias
    coef = pd.read_csv(saida / "coeficientes.csv")            # coeficientes
    mod = pd.read_csv(saida / "modelos.csv").set_index("modelo")  # modelos
    painel = pd.read_csv(saida / "painel_completo.csv")       # painel principal com variáveis
    V = cfg.FUNDAMENTOS                                       # fundamentos
    pc = coef[coef.modelo.eq("principal")].set_index("variavel").loc[V]  # coeficientes do principal
    ols = smf.ols("ln_mcap ~ roe_lag + dl_lag + size_lag + C(ticker) + C(ano)", data=painel).fit(  # LSDV no statsmodels
        cov_type="cluster", cov_kwds={"groups": pd.factorize(painel.ticker)[0]}, use_t=True)   # CR1, t(G−1)
    R.num("statsmodels: coeficientes", ols.params[V], pc.coef)  # compara
    R.num("statsmodels: erro-padrão CR1", ols.bse[V], pc.se_CR1)  # compara
    R.num("statsmodels: p CR1 com t(13)", ols.pvalues[V], pc.p_CR1)  # compara
    pn = painel.set_index(["ticker", "ano"])                  # índice empresa-ano
    m = PanelOLS(pn.ln_mcap, pn[V], entity_effects=True, time_effects=True)  # efeitos de empresa e de ano
    rc = m.fit(cov_type="clustered", cluster_entity=True, debiased=True, group_debias=True)  # CR1 com G/(G−1)
    R.num("linearmodels: coeficientes", rc.params[V], pc.coef)  # compara
    R.num("linearmodels: erro-padrão CR1", rc.std_errors[V], pc.se_CR1)  # compara
    R.num("linearmodels: R² intra-grupo", [rc.rsquared_within], [mod.loc["principal", "R2_intra"]])  # compara
    R.num("linearmodels: R² global", [rc.rsquared_inclusive], [mod.loc["principal", "R2_global"]])  # compara
    for bw in cfg.DEFASAGENS_DK:                              # 1 e 2 defasagens
        rk = m.fit(cov_type="kernel", kernel="bartlett", bandwidth=bw, debiased=True)  # Driscoll–Kraay no linearmodels
        R.num(f"linearmodels: Driscoll–Kraay, {bw} defasagem(ns)", rk.std_errors[V], pc[f"se_DK{bw}"])  # compara


def texto_do_tcc(R: Registro, saida):                         # conferência C
    """C. Cada valor impresso no TCC, recalculado com as mesmas casas decimais."""
    print("\nC. Resultados × valores publicados no TCC")      # título
    pub = pd.read_csv(cfg.DADOS / "documentos" / "valores_publicados_tcc.csv", dtype=str, keep_default_na=False)  # 465 valores publicados
    pub["calculado"] = [formatar(valor(c, saida), dc, t) for c, dc, t in zip(pub.chave, pub.decimais, pub.tipo)]  # recalcula e formata
    pub["confere"] = pub.calculado == pub.publicado         # comparação do texto formatado
    pub.to_csv(saida / "conferencia_tcc.csv", index=False)    # grava conferencia_tcc.csv
    for tab, g in pub.groupby("tabela", sort=False):        # um resumo por tabela
        ok = bool(g.confere.all())                            # tabela inteira confere?
        print(f"  [{'ok' if ok else 'FALHA'}] {tab:42s} {int(g.confere.sum())} de {len(g)} valores")  # linha do relatório
        if not ok:                                            # falhou
            R.falhas.append(tab)                              # registra
            print(g[~g.confere][["linha", "item", "publicado", "calculado"]].to_string(index=False))  # mostra as divergências


def executar(saida=cfg.RESULTADOS) -> bool:                   # as três conferências
    """Roda as três conferências e informa o resultado."""
    R = Registro()                                            # acumulador
    pacote_original(R, saida)                                 # A
    bibliotecas(R, saida)                                     # B
    texto_do_tcc(R, saida)                                    # C
    print("\n" + ("TUDO CONFERIDO." if not R.falhas else f"{len(R.falhas)} FALHA(S): {R.falhas}"))  # resultado final
    return not R.falhas                                       # True se tudo coincidir
