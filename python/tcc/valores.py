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
    apa_n|ticker                  observações da empresa no painel principal (Apêndice A, Tabela 1)
    apa_total|companhias ou obs   nota do Apêndice A, Tabela 1 (14 e 76)
    apa_elegiveis|ticker          exercícios elegíveis em 2020–2025 (Apêndice A, Tabela 2)
    param|nome                    parâmetros citados nas Tabelas 2 e 3 (percentis, mínimo de anos)
    rubrica|conta                 código CVM da conta, só se ela existe nos extratos (Apêndice B)

Tipos de formatação: num (casas decimais), p ("< 0,0001" se menor), p_estrela (com "*"
se p < 0,05), abs (valor absoluto), int, ngk, texto (sem mudança), extenso ("dois").
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
    from .tabelas import elegibilidade                        # evita importação circular no topo
    r["el"] = elegibilidade(saida)                            # contagens por empresa (Apêndice A)
    r["rub"] = rubricas_nos_dados()                           # rubricas presentes nos extratos (Apêndice B)
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
    if k[0] == "apa_n":                                       # Apêndice A, Tabela 1
        return int((r["d"].ticker == k[1]).sum())             # observações da empresa no painel principal
    if k[0] == "apa_total":                                   # nota do Apêndice A, Tabela 1
        return r["d"].ticker.nunique() if k[1] == "companhias" else len(r["d"])  # 14 companhias ou 76 observações
    if k[0] == "apa_elegiveis":                               # Apêndice A, Tabela 2
        return int(r["el"].loc[k[1], "elegiveis"])            # exercícios elegíveis em 2020–2025
    if k[0] == "param":                                       # parâmetros citados nas Tabelas 2 e 3
        return {"winsor_inf": 100 * C.PERCENTIS_WINSOR[0], "winsor_sup": 100 * C.PERCENTIS_WINSOR[1],  # percentis 1 e 99
                "min_exercicios": C.MIN_EXERCICIOS}[k[1]]     # mínimo de quatro anos
    if k[0] == "rubrica":                                     # Apêndice B, Tabela 1
        return r["rub"].get(k[1], "")                         # código da conta, se ela de fato existe nos dados
    raise KeyError(chave)                                     # chave desconhecida


def rubricas_nos_dados():                                     # conta → código, só se presente
    """Código de cada rubrica do Apêndice B, mantido só se a conta existe nos extratos da CVM
    na demonstração indicada (assim a conferência prova que a tabela descreve os dados usados)."""
    import glob                                               # lista de arquivos
    c = pd.read_csv(C.DADOS / "cvm" / "contas_cvm.csv", dtype={"CD_CONTA": str}, usecols=["CD_CONTA", "GRUPO_DFP"])  # extrato principal
    a = pd.concat(pd.read_csv(f, dtype={"CD_CONTA": str}, usecols=["CD_CONTA", "GRUPO_DFP"])  # extratos complementares
                  for f in sorted(glob.glob(str(C.DADOS / "cvm_complementar" / "complementos_*.csv"))))  # (1.01.02)
    pares = set(zip(pd.concat([c, a]).CD_CONTA, pd.concat([c, a]).GRUPO_DFP.str.split(" - ", n=1).str[1]))  # (código, demonstração)
    return {conta: cod for conta, dem, cod in C.RUBRICAS if (cod, C.DEMONSTRACOES[dem]) in pares}  # só as encontradas


EXTENSO = ["zero", "um", "dois", "três", "quatro", "cinco", "seis"]  # números que o TCC escreve por extenso


def formatar(x, dec, tipo):                                   # formato do TCC
    """Formato do TCC: vírgula decimal, sinal de menos tipográfico (−), '< 0,0001' e asterisco."""
    if tipo in ("ngk", "texto"):                              # texto pronto (N/G/K ou código de conta)
        return x                                              # sem mudança
    if tipo == "extenso":                                     # inteiro escrito por extenso no TCC
        return EXTENSO[int(x)]                                # ex.: 2 → "dois"
    if tipo == "int":                                         # inteiro
        return str(int(x))                                    # sem casas
    if tipo in ("p", "p_estrela") and x < 1e-4:               # p muito pequeno
        return "< 0,0001"                                     # como no texto
    if tipo == "abs":                                         # valor absoluto
        x = abs(x)                                            # ex.: "6,16% menos"
    s = f"{x:.{int(dec)}f}".replace(".", ",").replace("-", "−")  # vírgula decimal e sinal −
    return s + ("*" if tipo == "p_estrela" and x < C.NIVEL else "")  # asterisco da Tabela 7
