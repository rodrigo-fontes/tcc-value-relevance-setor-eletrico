# =============================================================================
# contabil.R — Contas da CVM e fundamentos contábeis (eqs. 3 a 6; Tabela 3 e Apêndice B do TCC)
# =============================================================================
#
#   (3)  ROE_it    = LL_it / PL_it                  LL: lucro da controladora; PL: seu patrimônio no encerramento
#   (4)  EBITDA_it = EBIT_it + |DA_it|              EBIT: resultado antes do financeiro e dos tributos; DA da DVA
#   (5)  AL_it     = (DCP_it + DLP_it − CX_it) / EBITDA_it     em "vezes"
#   (6)  PORTE_it  = ln(AT_it)                      AT: ativo total em reais
#
# Contas (plano padronizado da CVM): AT = 1 · CX = 1.01.01 · DCP = 2.01.04 · DLP = 2.02.01 ·
# PL total = 2.03 · não controladores = 2.03.09 · EBIT = 3.05 · lucro total = 3.11 ·
# controladora = 3.11.01 · não controladores = 3.11.02 · DA = 7.04.01.
#
# Rentabilidade, alavancagem e porte (Penman, 2013); patrimônio e lucro são os
# elementos contábeis do modelo de Ohlson (1995). Equivale a python/tcc/contabil.py.
# =============================================================================

montar_financeiro <- function(d) {                         # fundamentos por empresa-exercício
  contas <- d$contas                                       # formato longo: uma linha por conta
  chave <- unique(contas[, c("CD_CVM", "ano", "escopo")])  # empresa-exercício (um escopo por par)
  chave <- chave[order(chave$CD_CVM, chave$ano, chave$escopo, method = "radix"), ]   # mesma ordem do pandas.pivot
  fin <- chave                                             # base da tabela larga
  for (cta in sort(unique(contas$CD_CONTA), method = "radix")) {                   # uma coluna por conta
    x <- contas[contas$CD_CONTA == cta, ]                  # valores da conta
    fin[[cta]] <- x$valor[match(paste(fin$CD_CVM, fin$ano, fin$escopo), paste(x$CD_CVM, x$ano, x$escopo))]  # valor da conta em cada empresa-exercício
  }
  idx <- match(fin$CD_CVM, d$universo$CD_CVM)              # liga ao cadastro
  fin$CNPJ_CIA <- d$universo$CNPJ_CIA[idx]; fin$ticker <- d$universo$ticker[idx]   # CNPJ e ticker
  fin <- fin[!is.na(idx), ]; rownames(fin) <- NULL         # só empresas do cadastro
  con <- fin$escopo == "con"                               # consolidado?
  fin$pl_controladora <- ifelse(con, fin[["2.03"]] - fin[["2.03.09"]], fin[["2.03"]])   # PL = 2.03 − 2.03.09
  fin$lucro_controladora <- ifelse(con, fin[["3.11.01"]], fin[["3.11"]])              # LL = 3.11.01
  r <- conciliar_lucro(fin)                                # corrige parcelas inconsistentes (Light, Serena)
  fin <- r$fin                                                # base corrigida
  pos_ou_na <- function(x) ifelse(verdade(x > 0), x, NA)   # denominador só se positivo
  fin$roe <- fin$lucro_controladora / pos_ou_na(fin$pl_controladora)                 # eq. (3), PL > 0
  fin$ebitda <- fin[["3.05"]] + abs(fin[["7.04.01"]])     # eq. (4): o módulo soma a DA registrada como negativa
  fin$dl <- (fin[["2.01.04"]] + fin[["2.02.01"]] - fin[["1.01.01"]]) / pos_ou_na(fin$ebitda)   # eq. (5), EBITDA > 0
  fin$size <- log(pos_ou_na(fin[["1"]]))                   # eq. (6): elasticidade, com o valor também em log
  list(fin = fin, correcoes = r$correcoes)                 # fundamentos e registro das correções
}

conciliar_lucro <- function(fin) {                         # lucro total = controladora + não controladores?
  registros <- list()                                      # valor anterior, valor usado e justificativa
  for (i in seq_len(nrow(fin))) {                          # cada empresa-exercício
    r <- fin[i, ]                                             # linha atual
    dif <- r[["3.11"]] - r[["3.11.01"]] - r[["3.11.02"]]   # quanto falta para fechar a soma
    if (r$escopo != "con" || !verdade(abs(dif) > TOLERANCIA_LUCRO)) next          # fecha (ou é individual)
    ind <- lucro_individual(r$ano)                         # DRE individual do exercício
    v <- NA_real_                                          # lucro individual, se houver
    if (!is.null(ind)) {                                      # há extrato da DRE individual
      ind <- ind[as.integer(ind$CD_CVM) == r$CD_CVM, ]     # a empresa
      ind <- ind[order(ind$VERSAO), ]                      # versões em ordem
      if (nrow(ind)) v <- ind$VL_CONTA[nrow(ind)] * c(MIL = 1000, UNIDADE = 1)[[ind$ESCALA_MOEDA[nrow(ind)]]]   # última, em reais
    }
    if (is.finite(v) && abs(v - r[["3.11"]]) <= TOLERANCIA_LUCRO && r[["3.11.02"]] == 0) {   # individual = total
      fin$lucro_controladora[i] <- v; st <- "confirmado_DRE_individual_igual_consolidado"   # Light 2021–2024; Serena 2021
    } else {                                                  # caso contrário
      fin$lucro_controladora[i] <- NA; st <- "excluido_lucro_inconsistente"               # Light 2025: fica ausente
    }
    registros[[length(registros) + 1]] <- data.frame(ticker = r$ticker, ano = r$ano, anterior = r$lucro_controladora,  # valor anterior, valor usado e justificativa
                                                     corrigido = fin$lucro_controladora[i], status = st)  # (continuação)
  }
  list(fin = fin, correcoes = do.call(rbind, registros))      # base e registro
}
