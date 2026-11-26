"""
tcc.capitalizacao — Capitalização de mercado por empresa-ano (eq. 1 do TCC)
===========================================================================

    VM_it = Σ_c P_ct × (Q_ct − T_ct)

    P: último preço nominal de dezembro da classe c (B3)
    Q: ações emitidas da classe c no encerramento (DFP conciliada com o FRE)
    T: ações da classe c mantidas em tesouraria

A capitalização mede o valor de mercado das ações (não inclui dívida). É a
medida de valor usada na literatura de relevância informacional em níveis
(Collins, Maydew e Weiss, 1997; Barth, Beaver e Landsman, 2001), em vez do
retorno, que depende também do preço inicial e dos proventos (Easton e
Harris, 1991; Kothari e Zimmerman, 1995).

Por que conciliar? Preço e quantidade vêm de fontes diferentes. Um erro de
escala (milhares × unidades), uma tesouraria já descontada ou um desdobramento
após dezembro mudam o valor sem nenhum aviso. Regra do TCC: divergência não
resolvida exclui a observação; nada é estimado ou extrapolado.

Status possíveis de cada empresa-ano (coluna `status`):
    ok                                      capitalização calculada
    excluir_capital_ambiguo_ou_ausente      FRE sem uma quantidade única
    excluir_preco_classe_ausente            alguma classe sem cotação de dezembro
    excluir_subclasses_ou_tesouraria        PNA/PNB sem repartição única documentada
    excluir_divergencia_tesouraria_DFP_FRE  tesouraria do FRE diferente da DFP
    excluir_divergencia_tesouraria_FRE      FRE com mais de um saldo de tesouraria
    excluir_tesouraria_nao_documentada      tesouraria ausente no FRE
    excluir_tesouraria_evento_posterior     evento posterior com tesouraria (não desfeito)
    excluir_quantidade_invalida             quantidade em circulação ≤ 0
"""
import json                                                 # serializa a repartição das subclasses
import numpy as np                                          # NaN e testes numéricos
import pandas as pd                                         # tabelas
from . import config as C                                   # parâmetros do estudo

COLUNAS = ["ticker", "ano", "status", "fonte", "escala", "emitidas_on", "emitidas_pn",  # ordem das colunas de capitalizacao.csv
           "tesouraria_on", "tesouraria_pn", "mcap", "nota"]   # ordem das colunas de capitalizacao.csv


def coincide(fre: pd.DataFrame, on: float, pn: float, tol: float) -> pd.DataFrame:  # filtro de quantidades iguais (DFP × FRE)
    """Linhas do FRE cujas quantidades ordinárias (ON) e preferenciais (PN) coincidem com (on, pn)."""
    return fre[(abs(fre.Quantidade_Acoes_Ordinarias - on) <= tol)          # ON dentro da tolerância
               & (abs(fre.Quantidade_Acoes_Preferenciais - pn) <= tol)]    # e PN dentro da tolerância


def tolerancia(escala: float) -> float:                       # tolerância conforme a escala documental
    """Tolerância de arredondamento: em milhares, até 999 ações; em unidades, praticamente exata."""
    return max(escala - 1, 0.01)                            # 1000 -> 999 ; 1 -> 0,01


def raiz_ticker(ticker: str, ano: int) -> str:                # código de negociação vigente no ano
    """Quatro letras do código; usa a raiz antiga se a empresa ainda negociava com outro ticker."""
    raiz = ticker[:4]                                       # ex.: "CMIG3" -> "CMIG"
    if raiz in C.RAIZ_ANTIGA and ano <= C.RAIZ_ANTIGA[raiz][1]:   # Engie até 2015, Eneva até 2012
        return C.RAIZ_ANTIGA[raiz][0]                       # "TBLE" ou "MPXE"
    return raiz                                             # caso geral


def escalas_da_empresa(fre: pd.DataFrame, dfp: pd.DataFrame) -> set:  # escala válida em algum ano da empresa
    """Escalas (1 ou 1000) que fazem a DFP coincidir com o FRE em ALGUM ano da empresa.
    Serve de desempate quando o ano isolado não confirma uma escala única."""
    achadas = set()                                         # escalas confirmadas
    for r in dfp.itertuples():                              # cada ano com DFP
        ff = fre[fre.Data_Autorizacao_Aprovacao <= f"{r.ano}-12-31"]      # capital aprovado até o fim do ano
        for esc in C.ESCALAS:                               # unidades e milhares
            if len(coincide(ff, r.QT_ACAO_ORDIN_CAP_INTEGR * esc, r.QT_ACAO_PREF_CAP_INTEGR * esc, tolerancia(esc))):  # a escala reproduz o FRE?
                achadas.add(esc)                            # esta escala reproduz o FRE
    return achadas                                            # conjunto {1}, {1000}, ambos ou vazio


def escala_do_ano(ff: pd.DataFrame, r) -> list:               # escala válida no próprio ano
    """Escalas confirmadas no próprio ano: emitidas, ou emitidas + tesouraria (DFP líquida)."""
    ok = []                                                 # escalas que coincidem
    for esc in C.ESCALAS:                                   # unidades e milhares
        tol = tolerancia(esc)                               # tolerância da escala
        bruto = coincide(ff, r.QT_ACAO_ORDIN_CAP_INTEGR * esc, r.QT_ACAO_PREF_CAP_INTEGR * esc, tol)  # FRE = emitidas da DFP
        liquido = coincide(ff, (r.QT_ACAO_ORDIN_CAP_INTEGR + r.QT_ACAO_ORDIN_TESOURO) * esc,  # FRE = emitidas + tesouraria (DFP já líquida)
                           (r.QT_ACAO_PREF_CAP_INTEGR + r.QT_ACAO_PREF_TESOURO) * esc, tol)  # mesma soma para as preferenciais
        if len(bruto) or len(liquido):                      # qualquer das duas confirma a escala
            ok.append(esc)                                    # guarda a escala confirmada
    return ok                                                 # lista de escalas do ano


def saldos_tesouraria(tes: pd.DataFrame, especie: str) -> np.ndarray:  # saldos de tesouraria informados no FRE
    """Saldos finais distintos de tesouraria informados no FRE para uma espécie (Ordinária/Preferencial)."""
    return tes[tes.Especie_Acao.eq(especie)].Quantidade_Final.dropna().unique()  # saldos distintos, sem ausentes


def quantidades_dfp(emp, ano, r, escala, ff, d, tes, notas):  # caminho principal (DFP conciliada)
    """Caminho principal: quantidades da DFP, na escala confirmada, conciliadas com o FRE.
    Devolve (on, pn, ton, tpn, status, match_fre)."""
    status = "ok"                                           # até prova em contrário
    on, pn = r.QT_ACAO_ORDIN_CAP_INTEGR * escala, r.QT_ACAO_PREF_CAP_INTEGR * escala      # emitidas
    ton, tpn = r.QT_ACAO_ORDIN_TESOURO * escala, r.QT_ACAO_PREF_TESOURO * escala          # tesouraria
    tol = tolerancia(escala)                                # tolerância da escala
    corte = f"{ano}-12-31"                                  # fim do exercício

    # 1) Evento societário entre 31/12 e 30/06 seguinte, já refletido na DFP: desfaz para casar com o preço de dezembro
    ev = d["eventos"]                                       # desdobramentos e grupamentos
    ev = ev[ev.CNPJ_Companhia.eq(emp.CNPJ_CIA) & (ev.Data_Aprovacao > corte)  # eventos da empresa aprovados após dezembro
            & (ev.Data_Aprovacao <= f"{ano + 1}-{C.JANELA_EVENTO}")].drop_duplicates(  # ... e até 30/06 do ano seguinte
        ["Data_Aprovacao", "Tipo_Evento", "Quantidade_Acoes_Ordinarias_Depois_Aprovacao",  # chave de duplicidade do evento
         "Quantidade_Acoes_Preferenciais_Depois_Aprovacao"])          # o FRE repete eventos entre versões
    for e in ev.itertuples():                               # cada evento candidato
        depois_on = abs(on - e.Quantidade_Acoes_Ordinarias_Depois_Aprovacao) <= tol      # DFP = quantidade pós-evento?
        depois_pn = abs(pn - e.Quantidade_Acoes_Preferenciais_Depois_Aprovacao) <= tol  # idem para as preferenciais
        if depois_on and depois_pn:                         # sim: a DFP já reflete o evento
            if ton or tpn:                                  # com tesouraria não há como desfazer com segurança
                status = "excluir_tesouraria_evento_posterior"  # evento + tesouraria: exclui
            else:                                           # volta à quantidade antes do evento
                on = e.Quantidade_Acoes_Ordinarias_Antes_Aprovacao  # ON antes do evento
                pn = e.Quantidade_Acoes_Preferenciais_Antes_Aprovacao  # PN antes do evento
                notas.append("desfeito_evento_" + e.Data_Aprovacao)  # registra a decisão

    # 2) Conferência com o FRE. Se só "emitidas + tesouraria" coincide, a DFP já vinha líquida (caso Neoenergia):
    #    recupera-se a quantidade emitida para não descontar a tesouraria duas vezes.
    match = coincide(ff, on, pn, tol)                       # FRE = emitidas?
    if len(match) == 0:                                     # não
        liquido = coincide(ff, on + ton, pn + tpn, tol)     # FRE = emitidas + tesouraria?
        if len(liquido):                                    # sim: DFP líquida
            match = liquido                                   # adota a linha do FRE que coincidiu
            notas.append("DFP_liquido_reconciliado_FRE")      # registra a decisão (Neoenergia 2021–2023)
    unicos = match[["Quantidade_Acoes_Ordinarias", "Quantidade_Acoes_Preferenciais"]].drop_duplicates()  # quantidades distintas no FRE
    if len(unicos) == 1:                                    # uma única quantidade no FRE
        on, pn = unicos.iloc[0].tolist()                    # adota a quantidade emitida do FRE

    # 3) Tesouraria: o saldo final no FRE precisa coincidir com o da DFP
    for especie, alvo in (("Ordinária", "on"), ("Preferencial", "pn")):
        vals = saldos_tesouraria(tes, especie)              # saldos distintos no FRE
        atual = ton if alvo == "on" else tpn                # saldo da DFP
        if len(vals) == 1:                                  # um saldo no FRE
            if abs(vals[0] - atual) <= tol:                 # coincide: usa o valor exato do FRE
                if alvo == "on":                              # qual espécie atualizar
                    ton = float(vals[0])                      # tesouraria ON do FRE
                else:                                         # senão
                    tpn = float(vals[0])                      # tesouraria PN do FRE
            else:                                           # diverge: exclui
                status = "excluir_divergencia_tesouraria_DFP_FRE"  # DFP ≠ FRE: exclui
        elif len(vals) > 1:                                 # FRE ambíguo: exclui
            status = "excluir_divergencia_tesouraria_FRE"     # FRE ambíguo: exclui

    # 4) Cemig 2020: quantidades conferidas na nota 26 das demonstrações (Cemig, 2021)
    if emp.ticker == "CMIG3" and ano == 2020:
        q = C.CEMIG_2020                                    # valores do documento original
        on, pn, ton, tpn = q["on"], q["pn"], q["ton"], q["tpn"]  # substitui pelas quantidades do documento
        status = "ok"                                         # observação válida
        notas.append("nota26_2020")                           # registra a fonte
    return on, pn, ton, tpn, status, match                    # quantidades, situação e linhas do FRE


def quantidades_fre(emp, ano, ff, tes, notas):                # caminho alternativo (só FRE)
    """Caminho alternativo (sem DFP conciliável): última aprovação do FRE do ano.
    Devolve (on, pn, ton, tpn, status, match_fre) ou None se o capital for ambíguo."""
    ff = ff[(ff.arquivo_ano >= ano) & (ff.arquivo_ano <= ano + 1)]       # formulários do ano e do seguinte
    if len(ff):                                             # fica com a aprovação mais recente
        ff = ff[ff.Data_Autorizacao_Aprovacao.eq(ff.Data_Autorizacao_Aprovacao.max())]  # última aprovação do capital
    unicos = ff[["Quantidade_Acoes_Ordinarias", "Quantidade_Acoes_Preferenciais"]].drop_duplicates()  # quantidades distintas
    if len(unicos) != 1:                                    # nenhuma ou várias quantidades: não há como decidir
        return None                                           # sinaliza capital ambíguo ou ausente
    on, pn = unicos.iloc[0].tolist()                        # quantidade emitida

    def tes_especie(especie, emitidas):                     # tesouraria da espécie
        if emitidas == 0:                                   # sem ações da espécie, sem tesouraria
            return 0                                          # tesouraria nula
        v = saldos_tesouraria(tes, especie)                 # saldos no FRE
        return float(v[0]) if len(v) == 1 else np.nan       # ausente ou ambíguo = não documentado

    ton, tpn = tes_especie("Ordinária", on), tes_especie("Preferencial", pn)  # tesouraria de cada espécie
    if emp.ticker == "ENBR3" and ano in (2010, 2011):       # EDP: DF de 2011, nota 26, p. 26 (EDP, 2012)
        q = C.EDP_2010_2011                                   # quantidades do documento original
        on, pn, ton, tpn = q["on"], q["pn"], q["ton"], q["tpn"]  # substitui pelas quantidades do documento
        notas.append("DF2011_nota26_p26")                     # registra a fonte
    status = "excluir_tesouraria_nao_documentada" if np.isnan(ton) or np.isnan(tpn) else "ok"  # sem tesouraria documentada: exclui
    return on, pn, ton, tpn, status, ff                       # quantidades, situação e linhas do FRE


def quantidades_por_classe(raiz, on, pn, ton, tpn, pp, match, d, status):  # quantidade em circulação por ticker
    """Quantidade em circulação por ticker de classe. Devolve ({ticker: quantidade}, status).

    ON usa o sufixo 3. Uma preferencial única usa o ticker PN cotado (sufixo 4).
    Subclasses PNA/PNB (sufixos 5 e 6) exigem uma única repartição documentada no FRE."""
    qtd = {raiz + "3": on - ton}                            # ordinárias em circulação
    if pn <= 0:                                             # sem preferenciais
        return qtd, status                                    # devolve as quantidades
    gen = pp[pp.classe.str.match(r"PN(?:\s|$)")]            # preferencial "genérica" (classe PN) cotada em dezembro
    if len(gen) == 1:                                       # existe: uma classe só
        qtd[gen.iloc[0].ticker] = pn - tpn                    # preferenciais em circulação
        return qtd, status                                    # devolve as quantidades
    opcoes = set()                                          # reparticoes PNA/PNB possíveis
    for fr in match.itertuples():                           # cada linha do FRE que confirmou o capital
        cc = d["classes_fre"]                                 # subclasses informadas no FRE
        cc = cc[cc.ID_Capital_Social.eq(fr.ID_Capital_Social) & cc.arquivo_ano.eq(fr.arquivo_ano)].drop_duplicates(  # da mesma linha de capital e formulário
            ["Tipo_Classe_Acao_Preferencial", "Quantidade_Acoes"])  # sem repetições
        if len(cc) == 0 or abs(cc.Quantidade_Acoes.sum() - pn) > .5:    # subclasses não somam o total de PN
            continue                                          # passa ao próximo item
        op, ruim = {}, False                                # repartição desta linha
        for cr in cc.itertuples():                            # cada subclasse
            tipo = str(cr.Tipo_Classe_Acao_Preferencial)    # "Preferencial Classe A", "... Classe B"
            suf = "5" if tipo.endswith("Classe A") else "6" if tipo.endswith("Classe B") else None  # PNA → sufixo 5; PNB → sufixo 6
            if suf is None:                                 # outra subclasse: não sabemos o ticker
                ruim = True                                   # marca a repartição como inválida
                break                                         # interrompe a leitura das subclasses
            op[raiz + suf] = int(cr.Quantidade_Acoes)         # quantidade da subclasse
        if not ruim:                                          # repartição válida
            opcoes.add(json.dumps(op, sort_keys=True))      # guarda como texto para comparar repartições
    if len(opcoes) != 1 or tpn != 0:                        # nenhuma, várias, ou tesouraria em subclasse
        return qtd, "excluir_subclasses_ou_tesouraria"        # Copel e Eletrobras na maior parte dos anos
    qtd.update(json.loads(next(iter(opcoes))))              # adiciona PNA e PNB
    return qtd, status                                        # devolve as quantidades


def calcular(d: dict):                                        # capitalização de todas as empresas-ano
    """Capitalização de todas as empresas-ano. Devolve (capitalizacao, componentes)."""
    linhas, componentes = [], []                            # saídas
    fre_tipo = d["cap_fre"].Tipo_Capital.str.contains("Integralizado|Emitido|Subscrito", na=False)  # capital integralizado, emitido ou subscrito
    for emp in d["universo"].itertuples():                  # 23 emissoras
        fre = d["cap_fre"][d["cap_fre"].CNPJ_Companhia.eq(emp.CNPJ_CIA) & fre_tipo]   # capital da empresa no FRE
        dfp = d["cap_dfp"][d["cap_dfp"].CNPJ_CIA.eq(emp.CNPJ_CIA)]                     # composição do capital na DFP
        escalas_emp = escalas_da_empresa(fre, dfp)          # escalas confirmadas em algum ano
        for ano in C.ANOS_COLETA:                           # 2010–2025
            notas = []                                      # registro das decisões
            raiz = raiz_ticker(emp.ticker, ano)             # raiz do código no ano
            ff = fre[fre.Data_Autorizacao_Aprovacao <= f"{ano}-12-31"]   # capital vigente até dezembro
            rr = dfp[dfp.ano.eq(ano)]                       # DFP do ano (no máximo uma linha)
            tes = d["tesouraria"]                             # movimentação de tesouraria (FRE)
            tes = tes[tes.CNPJ_Companhia.eq(emp.CNPJ_CIA) & tes.ano_saldo.eq(ano)]   # tesouraria do ano
            escalas_ano = escala_do_ano(ff, rr.iloc[0]) if len(rr) == 1 else []  # escalas confirmadas no ano
            escala = escalas_ano[0] if len(escalas_ano) == 1 else (  # escala única do ano; senão, a da empresa
                next(iter(escalas_emp)) if len(escalas_emp) == 1 else None)            # desempate pela empresa
            if len(rr) == 1 and escala:                     # caminho principal: DFP
                fonte = "DFP"                                 # origem da quantidade
                on, pn, ton, tpn, status, match = quantidades_dfp(emp, ano, rr.iloc[0], escala, ff, d, tes, notas)  # quantidades conciliadas
            else:                                           # caminho alternativo: FRE histórico
                fonte, escala = "FRE_historico", 1            # origem alternativa, sempre em unidades
                q = quantidades_fre(emp, ano, ff, tes, notas)  # quantidades do FRE
                if q is None:                               # capital ambíguo ou ausente
                    linhas.append(dict(ticker=emp.ticker, ano=ano, status="excluir_capital_ambiguo_ou_ausente"))  # registra a exclusão
                    continue                                  # passa ao próximo item
                on, pn, ton, tpn, status, match = q           # desempacota
            pp = d["precos"]                                  # cotações de dezembro (B3)
            pp = pp[pp.ano.eq(ano) & pp.ticker.str.startswith(raiz)]          # cotações das classes da empresa
            qtd, status = quantidades_por_classe(raiz, on, pn, ton, tpn, pp, match, d, status)  # quantidade por ticker de classe
            valor, comp = 0.0, []                           # soma P × (Q − T) por classe
            for tk, q in qtd.items():                         # cada classe de ação
                pr = pp[pp.ticker.eq(tk)]                   # preço da MESMA classe
                if q <= 0:                                  # quantidade inválida (NaN não entra aqui)
                    status = "excluir_quantidade_invalida"    # Q − T ≤ 0: exclui
                    continue                                  # passa ao próximo item
                if len(pr) != 1:                            # sem cotação: não se usa a de outra classe
                    status = "excluir_preco_classe_ausente"   # sem cotação da classe: exclui
                    continue                                  # passa ao próximo item
                pr = pr.iloc[0]                               # linha única de preço
                valor += q * pr.preco                       # P × (Q − T)
                comp.append(dict(ticker=emp.ticker, ano=ano, ticker_classe=tk, quantidade=q, preco=pr.preco,  # componente P × (Q − T) da classe
                                 data=int(pr.data), valor_classe=q * pr.preco))  # data do negócio usado
            linhas.append(dict(ticker=emp.ticker, ano=ano, status=status, fonte=fonte, escala=escala,  # uma linha por empresa-ano
                               emitidas_on=on, emitidas_pn=pn, tesouraria_on=ton, tesouraria_pn=tpn,  # quantidades usadas
                               mcap=valor if status == "ok" else np.nan, nota=";".join(notas)))  # VM só se a observação for válida
            if status == "ok":                                # observação válida
                componentes += comp                         # só guarda componentes de observações válidas
    cap = pd.DataFrame(linhas, columns=COLUNAS)             # colunas sempre na mesma ordem
    comp = pd.DataFrame(componentes)                          # tabela de componentes
    return aplicar_cpfl(cap, comp, d)                         # acrescenta os exercícios documentados da CPFL


def aplicar_cpfl(cap: pd.DataFrame, comp: pd.DataFrame, d: dict):  # CPFL: documentos originais
    """CPFL 2012 e 2014–2019: quantidades transcritas das DFs originais (CPFL Energia, 2013–2020; 6-K na SEC).
    Só ações ordinárias, sem tesouraria (Novo Mercado)."""
    for src in d["cpfl"].to_dict("records"):                # cada exercício documentado
        ano, on = int(src["ano"]), int(src["emitidas"])       # exercício e ações emitidas
        pr = d["precos"][d["precos"].ticker.eq("CPFE3") & d["precos"].ano.eq(ano)].iloc[0]   # cotação de dezembro
        i = cap.index[cap.ticker.eq("CPFE3") & cap.ano.eq(ano)][0]        # linha a substituir
        for k, v in dict(status="ok", fonte="DFP_original_SEC", emitidas_on=on, emitidas_pn=0, tesouraria_on=0,  # campos da linha corrigida
                         tesouraria_pn=0, mcap=on * pr.preco, nota=src["url"]).items():  # VM = P × Q; a URL fica como nota
            cap.loc[i, k] = v                               # substitui campo a campo
        comp = pd.concat([comp, pd.DataFrame([dict(ticker="CPFE3", ano=ano, ticker_classe="CPFE3", quantidade=on,  # acrescenta o componente
                                                   preco=pr.preco, data=int(pr.data), valor_classe=on * pr.preco)])],  # preço e valor da classe
                         ignore_index=True)                   # renumera as linhas
    return cap, comp                                          # capitalização e componentes
