"""
tcc.valores — Uma chave para cada número do TCC
===============================================

Cada número citado no TCC tem uma chave textual, usada em dois lugares:
    • dados/documentos/valores_publicados_tcc.csv — conferência com o texto;
    • relatorio/roteiro.txt — números inseridos no relatório com {chave;decimais;tipo}.

Gramática das chaves (campos separados por "|"):
    coef|modelo|variavel          também se_CR1, p_CR1, p_WCR, p_DK1, p_DK2, IC_inf, IC_sup,
                                  excedencias, combinacoes
    mod|campo|modelo              N, G, K, gl_residuo, R2_global, R2_intra, R2_parcial
    ngk|modelo                    texto "N/G/K", ex.: 76/14/22
    holm|variavel                 p WCR ajustado por Holm
    desc|estatistica|variavel     media, dp, min, mediana, max de mcap_bi, ln_mcap, roe_pct, dl_lag, size_lag
    vif|variavel                  VIF intra-grupo
    fwl|ticker                    % da variação do ROE vinda da empresa
    fwl_obs|ticker|ano            % vinda de uma observação (CEB 2022 = 31,38)
    efeito|variavel               eq. (8) em %: ROE +10 p.p., AL +1 vez, ativo +10%
    media_bruta|coluna            média sem winsorização (dívida e dívida ampliada)
    funil|etapa                   contagens do funil (138, 90, 84, 76)
    contagem|coluna               linhas significativas na Tabela 7 (12, 13, 15)
    cobertura|painel|ano          empresas por ano (Tabela 1); ano = total para o N

Tipos de formatação: num (casas decimais), p ("< 0,0001" se menor), p_estrela (com "*"
se p < 0,05), abs (valor absoluto), int, ngk.
"""
import json                                                   # JSON
from functools import lru_cache                             # lê os resultados uma vez só
import numpy as np                                            # exp
import pandas as pd                                           # tabelas
from . import config as C                                     # pasta de resultados e nível


@lru_cache(maxsize=None)                                      # memoriza por pasta
def _res(saida):                                              # carrega resultados
    """Carrega os resultados necessários (com cache por pasta)."""
    r = {}                                                    # dicionário de tabelas
    r["coef"] = pd.read_csv(saida / "coeficientes.csv").set_index(["modelo", "variavel"])  # coeficientes
    r["mod"] = pd.read_csv(saida / "modelos.csv").set_index("modelo")  # modelos
    r["d"] = pd.read_csv(saida / "painel_principal.csv")      # painel principal
    r["h"] = pd.read_csv(saida / "painel_historico.csv")      # painel histórico
    r["pc"] = pd.read_csv(saida / "painel_completo.csv")      # painel completo
    r["inf"] = pd.read_csv(saida / "influencia_observacoes.csv")  # influência
    r["ve"] = pd.read_csv(saida / "variacao_por_empresa.csv").set_index("ticker")  # frações por empresa
    r["hl"] = pd.read_csv(saida / "holm.csv").set_index("variavel")  # Holm
    r["dg"] = json.loads((saida / "diagnosticos.json").read_text())  # VIF
    r["fun"] = json.loads((saida / "funil.json").read_text())  # funil
    r["c7"] = json.loads((saida / "tabelas_tcc" / "tabela_7_contagem.json").read_text())["significativos"]  # contagens da Tabela 7
    return r                                                  # tudo carregado


def valor(chave: str, saida=C.RESULTADOS):                    # chave → valor
    """Valor (número ou texto) correspondente à chave."""
    r, k = _res(saida), chave.split("|")                      # resultados e campos da chave
    if k[0] in ("coef", "se_CR1", "p_CR1", "p_WCR", "p_DK1", "p_DK2", "IC_inf", "IC_sup", "excedencias", "combinacoes"):  # colunas de coeficientes.csv
        return r["coef"].loc[(k[1], k[2]), k[0]]           # coluna k[0] do modelo k[1], variável k[2]
    if k[0] == "mod":                                         # campos de modelos.csv
        return r["mod"].loc[k[2], k[1]]                     # campo k[1] do modelo k[2]
    if k[0] == "ngk":                                         # texto N/G/K
        return "/".join(str(int(r["mod"].loc[k[1], c])) for c in "NGK")  # ex.: 76/14/22
    if k[0] == "holm":                                        # Holm
        return r["hl"].loc[k[1], "p_Holm"]                    # p WCR ajustado
    if k[0] == "desc":                                      # Tabela 4
        d = r["d"]                                            # painel principal
        s = {"mcap_bi": d.mcap / 1e9, "ln_mcap": d.ln_mcap, "roe_pct": d.roe_lag * 100,  # série escolhida
             "dl_lag": d.dl_lag, "size_lag": d.size_lag}[k[2]]  # (continuação)
        return {"media": s.mean(), "dp": s.std(), "min": s.min(), "mediana": s.median(), "max": s.max()}[k[1]]  # estatística escolhida (desvio amostral)
    if k[0] == "vif":                                         # VIF
        return r["dg"]["VIF_intra"][k[1]]                     # VIF do fundamento
    if k[0] == "fwl":                                         # fração por empresa
        return 100 * r["ve"].loc[k[1], "fracao_variacao_roe_lag"]  # em %
    if k[0] == "fwl_obs":                                     # fração de uma observação
        i = r["inf"]                                          # tabela por observação
        return 100 * i[(i.ticker == k[1]) & (i.ano == int(k[2]))].fracao_variacao_roe_lag.iloc[0]  # em %
    if k[0] == "efeito":                                    # eq. (8)
        b = r["coef"].loc[("principal", k[1]), "coef"]        # coeficiente do principal
        return 100 * {"roe_lag": np.exp(b * .1) - 1, "dl_lag": np.exp(b) - 1, "size_lag": 1.1 ** b - 1}[k[1]]  # eq. (8)
    if k[0] == "media_bruta":                                 # média sem winsorização
        return r["pc"][k[1]].mean()                           # média da coluna
    if k[0] == "funil":                                       # funil
        return r["fun"][k[1]]                                 # contagem do funil
    if k[0] == "contagem":                                    # Tabela 7
        return r["c7"][k[1]]                                  # linhas com p < 0,05
    if k[0] == "cobertura":                                   # Tabela 1
        p = r["d"] if k[1] == "principal" else r["h"]         # painel escolhido
        return len(p) if k[2] == "total" else int((p.ano == int(k[2])).sum())  # N ou empresas do ano
    raise KeyError(chave)                                     # chave desconhecida


def formatar(x, dec, tipo):                                   # formato do TCC
    """Formato do TCC: vírgula decimal, sinal de menos tipográfico (−), '< 0,0001' e asterisco."""
    if tipo == "ngk":                                         # texto pronto
        return x                                              # sem mudança
    if tipo == "int":                                         # inteiro
        return str(int(x))                                    # sem casas
    if tipo in ("p", "p_estrela") and x < 1e-4:               # p muito pequeno
        return "< 0,0001"                                     # como no texto
    if tipo == "abs":                                         # valor absoluto
        x = abs(x)                                            # ex.: "6,16% menos"
    s = f"{x:.{int(dec)}f}".replace(".", ",").replace("-", "−")  # vírgula decimal e sinal −
    return s + ("*" if tipo == "p_estrela" and x < C.NIVEL else "")  # asterisco da Tabela 7
