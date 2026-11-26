"""
tcc.entradas — Leitura dos extratos congelados
==============================================

Todos os arquivos de `dados/` são lidos aqui, uma única vez, e devolvidos num
dicionário. Nenhuma etapa do pipeline acessa a internet: os extratos foram
congelados na coleta e seus arquivos brutos estão identificados por SHA-256
em `dados/fontes.json` e `dados/b3/manifesto_precos.json`.

Fontes (TCC, seção "Fontes de dados"):
    CVM (2026a) — DFP: contas contábeis e composição do capital.
    CVM (2026b) — FRE: capital social por classe, eventos e tesouraria.
    B3 (2026)   — COTAHIST: último negócio de dezembro, preço nominal.
"""
import pandas as pd                                         # leitura de CSV
from .config import DADOS                                   # pasta dados/


def carregar() -> dict:                                       # lê todos os extratos
    """Lê os extratos e devolve um dicionário {nome: DataFrame}."""
    d = {}                                                  # dicionário de saída
    cvm = DADOS / "cvm"                                     # subpasta com os extratos da CVM
    d["universo"] = pd.read_csv(cvm / "universo_identificado.csv")        # 23 emissoras: ticker, código CVM, CNPJ
    d["cap_dfp"] = pd.read_csv(cvm / "capital_dfp.csv")                   # ações emitidas e em tesouraria (DFP)
    d["cap_fre"] = pd.read_csv(cvm / "capital_social.csv")                # capital social (FRE)
    d["classes_fre"] = pd.read_csv(cvm / "capital_social_classe_acao.csv")  # preferenciais por subclasse (FRE)
    d["eventos"] = pd.read_csv(cvm / "capital_social_desdobramento.csv")  # desdobramentos e grupamentos (FRE)
    d["tesouraria"] = pd.read_csv(cvm / "valor_mobiliario_tesouraria_movimentacao.csv")  # tesouraria (FRE)
    d["tesouraria"]["ano_saldo"] = pd.to_datetime(                        # ano a que o saldo final se refere
        d["tesouraria"].Data_Fim_Exercicio_Social).dt.year    # fim do exercício → ano
    d["contas"] = pd.read_csv(cvm / "contas_cvm.csv")                     # 11 contas do DFP, já em reais
    d["precos"] = pd.read_csv(DADOS / "b3" / "precos_dezembro_2010_2025.csv")  # último negócio de dezembro
    d["cpfl"] = pd.read_csv(DADOS / "documentos" / "capital_cpfl_documentado.csv")  # CPFL: DFs originais (6-K)
    return d                                                # devolve tudo para as etapas seguintes


def lucro_individual(ano: int) -> pd.DataFrame | None:        # DRE individual de um exercício
    """DRE individual (conta 3.11) usada para conferir o lucro da controladora; None se não houver extrato."""
    arq = DADOS / "cvm_complementar" / f"lucro_individual_{ano}.csv"    # um arquivo por exercício (2021–2024)
    return pd.read_csv(arq) if arq.exists() else None                   # ausência = não há como conferir


def aplicacoes_financeiras() -> pd.DataFrame:                 # conta 1.01.02 por empresa-exercício
    """Conta 1.01.02 (aplicações financeiras) dos DFP complementares, última versão, em reais."""
    partes = []                                             # um DataFrame por ano
    for arq in sorted((DADOS / "cvm_complementar").glob("complementos_*.csv")):  # 2019–2024
        a = pd.read_csv(arq, dtype={"CD_CONTA": str})       # códigos de conta como texto (ex.: "1.01.02")
        a["ano"] = pd.to_datetime(a.DT_REFER).dt.year       # exercício de referência
        a = a[a.CD_CONTA.eq("1.01.02") & a.demonstracao.eq("BPA")]          # só aplicações financeiras do ativo
        a = a.sort_values("VERSAO").drop_duplicates(        # última versão de cada documento (reapresentações)
            ["CD_CVM", "ano", "escopo", "CD_CONTA"], keep="last")  # chave do documento; fica a última versão
        a["aplicacoes"] = a.VL_CONTA * a.ESCALA_MOEDA.map({"MIL": 1000, "UNIDADE": 1})  # converte para reais
        partes.append(a)                                    # guarda o ano
    return pd.concat(partes)[["CD_CVM", "ano", "escopo", "aplicacoes"]]  # junta os anos
