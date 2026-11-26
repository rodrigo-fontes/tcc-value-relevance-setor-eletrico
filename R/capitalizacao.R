# =============================================================================
# capitalizacao.R — Capitalização de mercado por empresa-ano (eq. 1 do TCC)
# =============================================================================
#
#   VM_it = Σ_c P_ct × (Q_ct − T_ct)
#
#   P: último preço nominal de dezembro da classe c (B3)
#   Q: ações emitidas da classe c no encerramento (DFP conciliada com o FRE)
#   T: ações da classe c em tesouraria
#
# A capitalização é a medida de valor da literatura de relevância informacional
# em níveis (Collins, Maydew e Weiss, 1997; Barth, Beaver e Landsman, 2001), e
# não o retorno, que depende do preço inicial e dos proventos (Easton e Harris,
# 1991; Kothari e Zimmerman, 1995).
#
# Por que conciliar? Preço e quantidade vêm de fontes diferentes: um erro de
# escala, uma tesouraria já descontada ou um desdobramento após dezembro mudam o
# valor sem aviso. Regra do TCC: divergência não resolvida exclui a observação.
# Os status possíveis estão listados em python/tcc/capitalizacao.py e no README.
# Equivale a python/tcc/capitalizacao.py.
# =============================================================================

COLUNAS_CAP <- c("ticker", "ano", "status", "fonte", "escala", "emitidas_on", "emitidas_pn",  # ordem das colunas de capitalizacao.csv
                 "tesouraria_on", "tesouraria_pn", "mcap", "nota")   # ordem das colunas de capitalizacao.csv

coincide <- function(fre, on, pn, tol) {                   # linhas do FRE com ON e PN iguais a (on, pn)
  fre[verdade(abs(fre$Quantidade_Acoes_Ordinarias - on) <= tol &       # ON dentro da tolerância
              abs(fre$Quantidade_Acoes_Preferenciais - pn) <= tol), , drop = FALSE]   # e PN dentro da tolerância
}
tolerancia <- function(escala) max(escala - 1, 0.01)       # em milhares, até 999 ações; em unidades, ~exata
pares_unicos <- function(fre) unique(fre[, c("Quantidade_Acoes_Ordinarias", "Quantidade_Acoes_Preferenciais")])  # quantidades distintas no FRE

raiz_ticker <- function(ticker, ano) {                     # código de negociação vigente no ano
  raiz <- substr(ticker, 1, 4)                             # ex.: "CMIG3" → "CMIG"
  if (!is.null(RAIZ_ANTIGA[[raiz]]) && ano <= RAIZ_ANTIGA[[raiz]][[2]]) return(RAIZ_ANTIGA[[raiz]][[1]])   # TBLE, MPXE
  raiz                                                     # caso geral
}

escalas_da_empresa <- function(fre, dfp) {                 # escalas válidas em ALGUM ano da empresa
  achadas <- c()                                           # escalas confirmadas
  for (i in seq_len(nrow(dfp))) {                          # cada ano com DFP
    r <- dfp[i, ]                                          # linha do ano
    ff <- fre[fre$Data_Autorizacao_Aprovacao <= paste0(r$ano, "-12-31"), ]   # capital aprovado até o fim do ano
    for (esc in ESCALAS) {                                 # unidades e milhares
      if (nrow(coincide(ff, r$QT_ACAO_ORDIN_CAP_INTEGR * esc, r$QT_ACAO_PREF_CAP_INTEGR * esc, tolerancia(esc))))  # a escala reproduz o FRE?
        achadas <- union(achadas, esc)                     # a escala reproduz o FRE
    }
  }
  achadas                                                  # c(), 1, 1000 ou ambas
}

escala_do_ano <- function(ff, r) {                         # escalas válidas no próprio ano
  ok <- c()                                                # escalas confirmadas
  for (esc in ESCALAS) {                                   # unidades e milhares
    tol <- tolerancia(esc)                                 # tolerância da escala
    bruto <- coincide(ff, r$QT_ACAO_ORDIN_CAP_INTEGR * esc, r$QT_ACAO_PREF_CAP_INTEGR * esc, tol)   # FRE = emitidas
    liquido <- coincide(ff, (r$QT_ACAO_ORDIN_CAP_INTEGR + r$QT_ACAO_ORDIN_TESOURO) * esc,          # FRE = emitidas
                        (r$QT_ACAO_PREF_CAP_INTEGR + r$QT_ACAO_PREF_TESOURO) * esc, tol)           # + tesouraria
    if (nrow(bruto) || nrow(liquido)) ok <- c(ok, esc)     # qualquer das duas confirma a escala
  }
  ok                                                          # escalas do ano
}

saldos_tesouraria <- function(tes, especie)                # saldos finais distintos no FRE
  unique(na.omit(tes$Quantidade_Final[verdade(tes$Especie_Acao == especie)]))  # saldos sem ausentes

quantidades_dfp <- function(emp, ano, r, escala, ff, d, tes, notas) {   # caminho principal: DFP conciliada
  status <- "ok"                                           # até prova em contrário
  on <- r$QT_ACAO_ORDIN_CAP_INTEGR * escala; pn <- r$QT_ACAO_PREF_CAP_INTEGR * escala     # emitidas
  ton <- r$QT_ACAO_ORDIN_TESOURO * escala; tpn <- r$QT_ACAO_PREF_TESOURO * escala         # tesouraria
  tol <- tolerancia(escala)                                # tolerância da escala
  corte <- paste0(ano, "-12-31")                           # fim do exercício

  # 1) Evento entre 31/12 e 30/06 seguinte, já refletido na DFP: desfaz para casar com o preço de dezembro
  ev <- d$eventos                                          # desdobramentos e grupamentos
  ev <- ev[ev$CNPJ_Companhia == emp$CNPJ_CIA & ev$Data_Aprovacao > corte &                    # da empresa, após dez.
           ev$Data_Aprovacao <= paste0(ano + 1, "-", JANELA_EVENTO), ]                       # e até 30/06
  ev <- ev[!duplicated(ev[, c("Data_Aprovacao", "Tipo_Evento", "Quantidade_Acoes_Ordinarias_Depois_Aprovacao",  # remove repetições do FRE
                              "Quantidade_Acoes_Preferenciais_Depois_Aprovacao")]), ]        # sem repetições do FRE
  for (i in seq_len(nrow(ev))) {                           # cada evento candidato
    e <- ev[i, ]                                           # linha do evento
    if (abs(on - e$Quantidade_Acoes_Ordinarias_Depois_Aprovacao) <= tol &&                    # DFP = quantidade
        abs(pn - e$Quantidade_Acoes_Preferenciais_Depois_Aprovacao) <= tol) {                 # depois do evento?
      if (ton != 0 || tpn != 0) {                          # com tesouraria não há como desfazer com segurança
        status <- "excluir_tesouraria_evento_posterior"       # evento + tesouraria: exclui
      } else {                                             # volta à quantidade antes do evento
        on <- e$Quantidade_Acoes_Ordinarias_Antes_Aprovacao   # ON antes do evento
        pn <- e$Quantidade_Acoes_Preferenciais_Antes_Aprovacao  # PN antes do evento
        notas <- c(notas, paste0("desfeito_evento_", e$Data_Aprovacao))                      # registra a decisão
      }
    }
  }

  # 2) Conferência com o FRE; se só "emitidas + tesouraria" coincide, a DFP já vinha líquida (Neoenergia)
  match_fre <- coincide(ff, on, pn, tol)                   # FRE = emitidas?
  if (nrow(match_fre) == 0) {                              # não
    liquido <- coincide(ff, on + ton, pn + tpn, tol)       # FRE = emitidas + tesouraria?
    if (nrow(liquido)) { match_fre <- liquido; notas <- c(notas, "DFP_liquido_reconciliado_FRE") }   # sim: DFP líquida
  }
  u <- pares_unicos(match_fre)                             # quantidades distintas no FRE
  if (nrow(u) == 1) { on <- u[1, 1]; pn <- u[1, 2] }       # adota a quantidade emitida do FRE

  # 3) Tesouraria: o saldo final no FRE precisa coincidir com o da DFP
  for (alvo in c("on", "pn")) {                            # cada espécie
    vals <- saldos_tesouraria(tes, if (alvo == "on") "Ordinária" else "Preferencial")   # saldos no FRE
    atual <- if (alvo == "on") ton else tpn                # saldo da DFP
    if (length(vals) == 1) {                               # um saldo no FRE
      if (abs(vals[1] - atual) <= tol) {                   # coincide: usa o valor exato do FRE
        if (alvo == "on") ton <- as.numeric(vals[1]) else tpn <- as.numeric(vals[1])  # valor exato do FRE
      } else status <- "excluir_divergencia_tesouraria_DFP_FRE"     # diverge: exclui
    } else if (length(vals) > 1) status <- "excluir_divergencia_tesouraria_FRE"   # ambíguo: exclui
  }

  # 4) Cemig 2020: quantidades conferidas na nota 26 das demonstrações (Cemig, 2021)
  if (emp$ticker == "CMIG3" && ano == 2020) {                 # Cemig 2020
    on <- CEMIG_2020$on; pn <- CEMIG_2020$pn; ton <- CEMIG_2020$ton; tpn <- CEMIG_2020$tpn   # documento original
    status <- "ok"; notas <- c(notas, "nota26_2020")       # válida, com a fonte registrada
  }
  list(on = on, pn = pn, ton = ton, tpn = tpn, status = status, match = match_fre, notas = notas)  # quantidades, situação, linhas do FRE e notas
}

quantidades_fre <- function(emp, ano, ff, tes, notas) {    # caminho alternativo: só FRE
  ff <- ff[ff$arquivo_ano >= ano & ff$arquivo_ano <= ano + 1, ]   # formulários do ano e do seguinte
  if (nrow(ff)) ff <- ff[ff$Data_Autorizacao_Aprovacao == max(ff$Data_Autorizacao_Aprovacao), ]   # última aprovação
  u <- pares_unicos(ff)                                    # quantidades distintas
  if (nrow(u) != 1) return(NULL)                           # nenhuma ou várias: capital ambíguo
  on <- u[1, 1]; pn <- u[1, 2]                             # quantidade emitida
  tes_especie <- function(especie, emitidas) {             # tesouraria de uma espécie
    if (emitidas == 0) return(0)                           # sem ações da espécie, sem tesouraria
    v <- saldos_tesouraria(tes, especie)                   # saldos no FRE
    if (length(v) == 1) as.numeric(v[1]) else NA_real_     # ausente ou ambíguo = não documentado
  }
  ton <- tes_especie("Ordinária", on); tpn <- tes_especie("Preferencial", pn)  # tesouraria de cada espécie
  if (emp$ticker == "ENBR3" && ano %in% c(2010, 2011)) {   # EDP: DF de 2011, nota 26, p. 26 (EDP, 2012)
    on <- EDP_2010_2011$on; pn <- EDP_2010_2011$pn; ton <- EDP_2010_2011$ton; tpn <- EDP_2010_2011$tpn  # quantidades do documento original
    notas <- c(notas, "DF2011_nota26_p26")                 # registra a fonte
  }
  status <- if (is.na(ton) || is.na(tpn)) "excluir_tesouraria_nao_documentada" else "ok"  # sem tesouraria documentada: exclui
  list(on = on, pn = pn, ton = ton, tpn = tpn, status = status, match = ff, notas = notas)  # quantidades e situação
}

quantidades_por_classe <- function(raiz, q, pp, d) {       # quantidade em circulação por ticker de classe
  qtd <- setNames(q$on - q$ton, paste0(raiz, "3"))         # ordinárias (sufixo 3)
  status <- q$status                                       # situação recebida
  if (q$pn <= 0) return(list(qtd = qtd, status = status))  # sem preferenciais
  gen <- pp[grepl("^PN(\\s|$)", pp$classe, perl = TRUE), ] # preferencial única (classe "PN") cotada em dezembro
  if (nrow(gen) == 1) {                                    # existe: uma classe só (sufixo 4)
    qtd[gen$ticker[1]] <- q$pn - q$tpn                        # preferenciais em circulação
    return(list(qtd = qtd, status = status))                  # devolve as quantidades
  }
  opcoes <- c()                                            # repartições PNA/PNB possíveis
  for (i in seq_len(nrow(q$match))) {                      # cada linha do FRE que confirmou o capital
    fr <- q$match[i, ]                                        # linha do FRE
    cc <- d$classes_fre[d$classes_fre$ID_Capital_Social == fr$ID_Capital_Social &           # subclasses da mesma
                        d$classes_fre$arquivo_ano == fr$arquivo_ano, ]                       # linha de capital
    cc <- cc[!duplicated(cc[, c("Tipo_Classe_Acao_Preferencial", "Quantidade_Acoes")]), ]   # sem repetições
    if (nrow(cc) == 0 || abs(sum(cc$Quantidade_Acoes) - q$pn) > .5) next                    # não somam o total de PN
    op <- c(); ruim <- FALSE                               # repartição desta linha
    for (m in seq_len(nrow(cc))) {                         # cada subclasse
      tipo <- cc$Tipo_Classe_Acao_Preferencial[m]          # "Preferencial Classe A", "... Classe B"
      suf <- if (verdade(endsWith(tipo, "Classe A"))) "5" else if (verdade(endsWith(tipo, "Classe B"))) "6" else NA  # PNA → 5; PNB → 6
      if (is.na(suf)) { ruim <- TRUE; break }              # outra subclasse: ticker desconhecido
      op[paste0(raiz, suf)] <- cc$Quantidade_Acoes[m]      # quantidade da subclasse
    }
    if (!ruim) { op <- op[order(names(op))]; opcoes <- union(opcoes, paste(names(op), op, sep = "=", collapse = ";")) }  # guarda a repartição como texto
  }
  if (length(opcoes) != 1 || is.na(q$tpn) || q$tpn != 0)  # nenhuma, várias, ou tesouraria em subclasse
    return(list(qtd = qtd, status = "excluir_subclasses_ou_tesouraria"))     # Copel e Eletrobras
  for (par in strsplit(opcoes, ";")[[1]]) { kv <- strsplit(par, "=")[[1]]; qtd[kv[1]] <- as.numeric(kv[2]) }   # PNA e PNB
  list(qtd = qtd, status = status)                            # quantidades e situação
}

calcular_capitalizacao <- function(d) {                    # capitalização de todas as empresas-ano
  linhas <- list(); componentes <- list()                  # saídas
  fre_tipo <- grepl("Integralizado|Emitido|Subscrito", d$cap_fre$Tipo_Capital)   # capital válido no FRE
  for (k in seq_len(nrow(d$universo))) {                   # 23 emissoras
    emp <- d$universo[k, ]                                    # emissora
    fre <- d$cap_fre[d$cap_fre$CNPJ_Companhia == emp$CNPJ_CIA & fre_tipo, ]       # capital da empresa no FRE
    dfp <- d$cap_dfp[d$cap_dfp$CNPJ_CIA == emp$CNPJ_CIA, ]                         # composição do capital na DFP
    escalas_emp <- escalas_da_empresa(fre, dfp)            # escalas confirmadas em algum ano
    for (ano in ANOS_COLETA) {                             # 2010–2025
      notas <- c()                                         # registro das decisões
      raiz <- raiz_ticker(emp$ticker, ano)                 # raiz do código no ano
      ff <- fre[fre$Data_Autorizacao_Aprovacao <= paste0(ano, "-12-31"), ]          # capital vigente até dezembro
      rr <- dfp[dfp$ano == ano, ]                          # DFP do ano
      tes <- d$tesouraria[d$tesouraria$CNPJ_Companhia == emp$CNPJ_CIA & d$tesouraria$ano_saldo == ano, ]   # tesouraria
      esc_ano <- if (nrow(rr) == 1) escala_do_ano(ff, rr[1, ]) else c()             # escalas do ano
      escala <- if (length(esc_ano) == 1) esc_ano[1] else if (length(escalas_emp) == 1) escalas_emp[1] else NA  # escala do ano; senão, a da empresa
      if (nrow(rr) == 1 && !is.na(escala)) {               # caminho principal: DFP
        fonte <- "DFP"                                        # origem da quantidade
        q <- quantidades_dfp(emp, ano, rr[1, ], escala, ff, d, tes, notas)  # quantidades conciliadas
      } else {                                             # caminho alternativo: FRE histórico
        fonte <- "FRE_historico"; escala <- 1                 # origem alternativa, em unidades
        q <- quantidades_fre(emp, ano, ff, tes, notas)        # quantidades do FRE
        if (is.null(q)) {                                  # capital ambíguo ou ausente
          linhas[[length(linhas) + 1]] <- data.frame(ticker = emp$ticker, ano = ano, status = "excluir_capital_ambiguo_ou_ausente")  # registra a exclusão
          next                                                # próxima iteração
        }
      }
      pp <- d$precos[d$precos$ano == ano & startsWith(d$precos$ticker, raiz), ]   # cotações das classes
      qc <- quantidades_por_classe(raiz, q, pp, d)         # quantidade por ticker
      status <- qc$status                                     # situação após as classes
      valor <- 0; comp <- list()                           # soma P × (Q − T)
      for (tk in names(qc$qtd)) {                          # cada classe
        qq <- qc$qtd[[tk]]                                 # quantidade em circulação
        pr <- pp[pp$ticker == tk, ]                        # preço da MESMA classe
        if (verdade(qq <= 0)) { status <- "excluir_quantidade_invalida"; next }     # (NA não conta como ≤ 0)
        if (nrow(pr) != 1) { status <- "excluir_preco_classe_ausente"; next }        # sem cotação: não substitui
        valor <- valor + qq * pr$preco                     # P × (Q − T)
        comp[[length(comp) + 1]] <- data.frame(ticker = emp$ticker, ano = ano, ticker_classe = tk, quantidade = qq,  # componente P × (Q − T)
                                               preco = pr$preco, data = pr$data, valor_classe = qq * pr$preco)  # preço, data do negócio e valor
      }
      linhas[[length(linhas) + 1]] <- data.frame(          # uma linha por empresa-ano
        ticker = emp$ticker, ano = ano, status = status, fonte = fonte, escala = escala,  # identificação
        emitidas_on = q$on, emitidas_pn = q$pn, tesouraria_on = q$ton, tesouraria_pn = q$tpn,  # quantidades usadas
        mcap = if (status == "ok") valor else NA, nota = paste(q$notas, collapse = ";"))  # VM só se válida
      if (status == "ok") componentes <- c(componentes, comp)    # só componentes de observações válidas
    }
  }
  cap <- do.call(rbind, lapply(linhas, function(x) {       # completa as colunas das linhas excluídas
    for (cc in setdiff(COLUNAS_CAP, names(x))) x[[cc]] <- NA  # colunas ausentes = NA
    x[, COLUNAS_CAP]                                          # ordem fixa
  }))
  aplicar_cpfl(cap, do.call(rbind, componentes), d)        # acrescenta os exercícios documentados da CPFL
}

aplicar_cpfl <- function(cap, comp, d) {                   # CPFL 2012 e 2014–2019: DFs originais (6-K na SEC)
  for (i in seq_len(nrow(d$cpfl))) {                       # cada exercício documentado
    ano <- d$cpfl$ano[i]; on <- d$cpfl$emitidas[i]         # exercício e ações emitidas (só ON, sem tesouraria)
    pr <- d$precos[d$precos$ticker == "CPFE3" & d$precos$ano == ano, ][1, ]      # cotação de dezembro
    k <- which(cap$ticker == "CPFE3" & cap$ano == ano)     # linha a substituir
    cap[k, c("status", "fonte", "nota")] <- list("ok", "DFP_original_SEC", d$cpfl$url[i])           # a URL vira nota
    cap[k, c("emitidas_on", "emitidas_pn", "tesouraria_on", "tesouraria_pn", "mcap")] <- list(on, 0, 0, 0, on * pr$preco)  # só ON, sem tesouraria; VM = P × Q
    comp <- rbind(comp, data.frame(ticker = "CPFE3", ano = ano, ticker_classe = "CPFE3", quantidade = on,  # acrescenta o componente
                                   preco = pr$preco, data = pr$data, valor_classe = on * pr$preco))  # preço, data e valor
  }
  list(cap = cap, comp = comp)                             # capitalização e componentes
}
