"""
tcc.contabil — Contas da CVM e fundamentos contábeis (eqs. 3 a 6, Tabela 3 e Apêndice B do TCC)
=================================================================================================

    (3)  ROE_it    = LL_it / PL_it                    LL: lucro atribuível à controladora; PL: seu patrimônio
                                                       líquido no encerramento (não a média dos saldos)
    (4)  EBITDA_it = EBIT_it + |DA_it|                EBIT: resultado antes do financeiro e dos tributos;
                                                       DA: depreciação, amortização e exaustão da DVA
    (5)  AL_it     = (DCP_it + DLP_it − CX_it) / EBITDA_it
                                                       DCP, DLP: empréstimos e financiamentos de curto e longo
                                                       prazo; CX: caixa e equivalentes. Em "vezes"
    (6)  PORTE_it  = ln(AT_it)                        AT: ativo total em reais

Contas do plano padronizado da CVM (Apêndice B, Tabela 1):
    AT = 1 · CX = 1.01.01 · DCP = 2.01.04 · DLP = 2.02.01 · PL total = 2.03 ·
    não controladores = 2.03.09 · EBIT = 3.05 · lucro total = 3.11 ·
    lucro da controladora = 3.11.01 · lucro dos não controladores = 3.11.02 · DA = 7.04.01

No consolidado, numerador e denominador do ROE pertencem aos mesmos
proprietários (os acionistas da controladora). Os três fundamentos
representam rentabilidade, alavancagem e porte (Penman, 2013); o patrimônio e
o lucro são os elementos contábeis do modelo de Ohlson (1995). A DA vem da DVA
porque a DRE padronizada não tem uma linha única para ela. O EBITDA é uma
aproximação: não reproduz EBITDA ajustado, regulatório ou geração de caixa.
"""
import numpy as np                                          # log, NaN
import pandas as pd                                         # tabelas
from . import config as C                                   # tolerâncias
from .entradas import lucro_individual                      # DRE individual (conferência do lucro)


def montar(d: dict) -> tuple[pd.DataFrame, pd.DataFrame]:     # fundamentos por empresa-exercício
    """Uma linha por empresa-exercício com contas, PL e lucro da controladora e os três fundamentos.
    Devolve (financeiro, correcoes_do_lucro)."""
    contas = d["contas"]                                    # formato longo: uma linha por conta
    fin = (contas.pivot(index=["CD_CVM", "ano", "escopo"], columns="CD_CONTA", values="valor")   # uma coluna por conta
           .reset_index()                                   # volta a ter CD_CVM, ano, escopo como colunas
           .merge(d["universo"][["CD_CVM", "CNPJ_CIA", "ticker"]], on="CD_CVM", validate="many_to_one"))  # acrescenta CNPJ e ticker
    consolidado = fin.escopo.eq("con")                      # o extrato tem um único escopo por empresa-ano
    # Patrimônio (PL) e lucro (LL) da CONTROLADORA, base da eq. (3)
    fin["pl_controladora"] = np.where(consolidado, fin["2.03"] - fin["2.03.09"], fin["2.03"])  # PL = 2.03 − 2.03.09 (consolidado) ou 2.03 (individual)
    fin["lucro_controladora"] = np.where(consolidado, fin["3.11.01"], fin["3.11"])  # LL = 3.11.01 (consolidado) ou 3.11 (individual)
    fin, correcoes = conciliar_lucro(fin)                   # corrige parcelas inconsistentes (Light, Serena)
    # Eq. (3) ROE = LL / PL, só com PL positivo (com PL ≤ 0 a razão não tem interpretação econômica)
    fin["roe"] = fin.lucro_controladora / fin.pl_controladora.where(fin.pl_controladora > 0)  # ROE = LL / PL (PL > 0)
    # Eq. (4) EBITDA = EBIT + |DA|: o módulo soma a DA mesmo quando registrada como negativa
    fin["ebitda"] = fin["3.05"] + abs(fin["7.04.01"])         # EBITDA = 3.05 + |7.04.01|
    # Eq. (5) AL = (DCP + DLP − CX) / EBITDA: exige EBITDA positivo; preserva posições líquidas de caixa (AL < 0)
    fin["dl"] = (fin["2.01.04"] + fin["2.02.01"] - fin["1.01.01"]) / fin.ebitda.where(fin.ebitda > 0)  # AL = (2.01.04 + 2.02.01 − 1.01.01) / EBITDA
    # Eq. (6) PORTE = ln(AT): com a capitalização também em log, o coeficiente é uma elasticidade
    fin["size"] = np.log(fin["1"].where(fin["1"] > 0))        # PORTE = ln(conta 1)
    return fin, correcoes                                     # fundamentos e registro das correções


def conciliar_lucro(fin: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:  # conciliação do lucro da controladora
    """Lucro total (3.11) deve ser controladora (3.11.01) + não controladores (3.11.02).

    Se a diferença passar de R$ 1 mil, consulta a DRE individual. Sendo ela igual ao
    lucro consolidado total e não havendo não controladores, o lucro individual é o
    da controladora (Light 2021–2024; Serena 2021). Caso contrário, o lucro fica
    ausente — nunca estimado."""
    registros = []                                          # valor anterior, valor usado e justificativa
    for i, r in fin.iterrows():                             # cada empresa-exercício
        diferenca = r["3.11"] - r["3.11.01"] - r["3.11.02"]   # quanto falta para fechar a soma
        if r.escopo != "con" or not abs(diferenca) > C.TOLERANCIA_LUCRO:   # fecha (ou é individual): nada a fazer
            continue                                          # lucro fecha: segue
        ind = lucro_individual(r.ano)                       # DRE individual do exercício
        v = np.nan                                          # lucro individual (se houver)
        if ind is not None:                                   # há extrato da DRE individual
            ind = ind[ind.CD_CVM.astype(int).eq(r.CD_CVM)].sort_values("VERSAO")   # empresa, versões em ordem
            if len(ind):                                      # empresa presente no extrato
                ult = ind.iloc[-1]                          # última versão
                v = float(ult.VL_CONTA) * {"MIL": 1000, "UNIDADE": 1}[ult.ESCALA_MOEDA]   # em reais
        if np.isfinite(v) and abs(v - r["3.11"]) <= C.TOLERANCIA_LUCRO and r["3.11.02"] == 0:  # individual = total consolidado e sem não controladores?
            fin.loc[i, "lucro_controladora"] = v            # confirmado: controladora = total consolidado
            status = "confirmado_DRE_individual_igual_consolidado"  # Light 2021–2024; Serena 2021
        else:                                                 # caso contrário
            fin.loc[i, "lucro_controladora"] = np.nan       # não conciliado: fica ausente
            status = "excluido_lucro_inconsistente"           # Light 2025
        registros.append(dict(ticker=r.ticker, ano=r.ano, anterior=r.lucro_controladora,  # valor anterior, valor usado e justificativa
                              corrigido=fin.loc[i, "lucro_controladora"], status=status))  # (continuação)
    return fin, pd.DataFrame(registros)                       # base corrigida e registro
