# =============================================================================
# especificacoes.R — Variáveis alternativas e catálogo de modelos (Tabelas 5 a 8 e Apêndice C)
# =============================================================================
# Cada modelo responde a uma pergunta econômica definida antes de olhar o valor de p;
# nenhum é escolhido pelo resultado (MacKinnon, Nielsen e Webb, 2023). Só o principal
# recebe Holm. A tabela "pergunta → modelo → tabela do TCC" está no cabeçalho de
# python/tcc/especificacoes.py e no README. Equivale àquele módulo.
# =============================================================================

painel_completo <- function(d, fin, comp) {                # painel principal + variáveis alternativas
  chave <- function(df, desloc = 0) paste(df$ticker, df$ano + desloc)        # chave empresa-ano
  k <- match(chave(d), chave(fin, 1))                      # exercício t−1 de cada observação
  pl <- fin$pl_controladora[k]                             # PL da controladora em t−1
  d$lnpl_lag     <- log(ifelse(pl > 0, pl, NA))            # ln(PL) (Tabela 8)
  d$roa_lag      <- fin[["3.11"]][k] / fin[["1"]][k]       # ROA líquido = lucro total / ativo (mesmo escopo)
  d$roa_oper_lag <- fin[["3.05"]][k] / fin[["1"]][k]       # ROA operacional = EBIT / ativo
  d$pl_bi_lag    <- pl / 1e9                               # modelo em níveis: PL em R$ bilhões
  d$ll_bi_lag    <- fin$lucro_controladora[k] / 1e9        # lucro em R$ bilhões (preserva prejuízos)
  d$mcap_bi      <- d$mcap / 1e9                           # capitalização em R$ bilhões
  for (v in c("roa_lag", "roa_oper_lag")) { d[[paste0(v, "_bruto")]] <- d[[v]]; d[[v]] <- winsorizar(d[[v]]) }   # ROAs winsorizados

  apl <- aplicacoes_financeiras()                          # conta 1.01.02 (CPC, 2010: 1.01.01 já tem equivalentes)
  ka <- match(paste(fin$CD_CVM, fin$ano, fin$escopo)[k], paste(apl$CD_CVM, apl$ano, apl$escopo))   # mesma empresa-exercício-escopo
  d$aplicacoes <- apl$aplicacoes[ka]                       # aplicações de t−1
  eb <- fin$ebitda[k]                                      # EBITDA de t−1
  d$dl_ampla_lag <- (fin[["2.01.04"]][k] + fin[["2.02.01"]][k] - fin[["1.01.01"]][k] - d$aplicacoes) /  # AL ampliada = (DCP + DLP − CX − aplicações) ...
    ifelse(eb > 0, eb, NA)                                 # AL ampliada = (DCP + DLP − CX − aplicações) / EBITDA
  d$dl_ampla_lag_bruto <- d$dl_ampla_lag                   # média bruta 2,2793 (vs. 2,5057)
  d$dl_ampla_lag <- winsorizar(d$dl_ampla_lag)             # winsorizada

  d$roe_media3 <- NA_real_; d$roe_plmedio <- NA_real_      # ROE médio de três anos e ROE com PL médio
  for (i in seq_len(nrow(d))) {                            # cada observação
    q <- fin[fin$ticker == d$ticker[i] & fin$ano %in% (d$ano[i] - 3:1), ]    # exercícios t−3, t−2, t−1
    q <- q[order(q$ano), ]                                 # em ordem
    if (nrow(q) == 3 && all(!is.na(q$roe)) && length(unique(q$escopo)) == 1 && q$escopo[3] == d$escopo_lag[i])  # três ROEs, escopo constante
      d$roe_media3[i] <- mean(q$roe)                       # três ROEs, escopo constante
    t1 <- fin[fin$ticker == d$ticker[i] & fin$ano == d$ano[i] - 1, ]         # PL final (t−1)
    t2 <- fin[fin$ticker == d$ticker[i] & fin$ano == d$ano[i] - 2, ]         # PL inicial (t−2)
    if (nrow(t1) == 1 && nrow(t2) == 1 && t1$escopo == t2$escopo &&  # dois exercícios no mesmo escopo
        verdade(t1$pl_controladora > 0) && verdade(t2$pl_controladora > 0))  # mesmo escopo e saldos positivos
      d$roe_plmedio[i] <- t1$lucro_controladora / ((t1$pl_controladora + t2$pl_controladora) / 2)  # LL(t−1) / média do PL inicial e final
  }
  for (v in c("roe_media3", "roe_plmedio")) { d[[paste0(v, "_bruto")]] <- d[[v]]; d[[v]] <- winsorizar(d[[v]]) }   # na amostra válida

  d$grupo <- ifelse(d$ticker %in% names(GRUPOS_SOCIETARIOS), GRUPOS_SOCIETARIOS[d$ticker], d$ticker)   # 12 grupos
  dmin <- aggregate(data ~ ticker + ano, comp, min)        # negócio mais antigo entre as classes
  d$data <- dmin$data[match(chave(d), chave(dmin))]        # data do último negócio usado
  d$dia_cotacao <- d$data %% 100                           # dia do mês
  d                                                           # painel completo
}

painel_contemporaneo <- function(d, fin) {                 # fundamentos do MESMO ano (retrospectivo)
  k0 <- match(paste(d$ticker, d$ano), paste(fin$ticker, fin$ano))           # exercício t
  c <- d                                                      # cópia do painel
  c$roe_atual <- fin$roe[k0]; c$dl_atual <- fin$dl[k0]; c$size_atual <- fin$size[k0]  # fundamentos do ano t
  c <- c[verdade(fin$pl_controladora[k0] > 0) & verdade(fin$ebitda[k0] > 0), ]   # PL e EBITDA positivos
  c <- c[complete.cases(c[, c("roe_atual", "dl_atual", "size_atual")]), ]        # 73 linhas
  for (v in c("roe_atual", "dl_atual")) c[[v]] <- winsorizar(c[[v]])         # limites da própria amostra
  c                                                           # painel contemporâneo
}

catalogo_modelos <- function(d, h, cont) {                 # lista de especificações, na ordem das saídas
  V <- FUNDAMENTOS                                            # ROE, AL e PORTE
  sem_winsor <- d                                          # ROE e AL sem winsorização
  for (v in V[1:2]) sem_winsor[[v]] <- sem_winsor[[paste0(v, "_bruto")]]  # valores brutos
  n_emp <- table(d$ticker)                                 # anos por empresa
  ceb <- d$ticker == "CEBR3"                               # linhas da CEB
  transicoes <- rep(FALSE, nrow(d))                        # janelas de eventos societários
  for (tk in names(TRANSICOES)) transicoes <- transicoes | (d$ticker == tk & d$ano %in% TRANSICOES[[tk]])  # marca CEB, Auren e Light
  VROA <- c("roa_lag", "dl_lag", "size_lag")               # ROA no lugar do ROE
  M <- function(nome, dados, vars = V, dep = "ln_mcap", grp = "ticker") list(nome = nome, dados = dados, vars = vars, dep = dep, grp = grp)  # atalho para uma especificação
  emps <- sort(unique(d$ticker), method = "radix")         # 14 empresas
  c(list(M("principal", d), M("sem_winsor", sem_winsor)),  # Tabelas 5–7
    lapply(emps, function(e) M(paste0("excluir_", e), d[d$ticker != e, ])),   # Figura 1; Ap. C 1
    list(M("sem_EKTR_TAEE", d[!d$ticker %in% c("EKTR3", "TAEE3"), ]),         # vínculos societários
         M("balanceado", d[d$ticker %in% names(n_emp)[n_emp == 6], ]),        # só empresas com seis anos
         M("cotacoes_desde_dia20", d[d$dia_cotacao >= DIA_MINIMO_COTACAO, ]),  # filtro de liquidez: 73
         M("historico", h),                                # 2012–2025
         M("historico_mesmas_empresas", h[h$ticker %in% d$ticker, ]),         # 89 linhas
         M("controle_PL", d, c(V, "lnpl_lag")),            # Tabela 8: + ln(PL)
         M("ROA", d, VROA),                                # Tabela 8: ROA líquido
         M("ROA_operacional", d, c("roa_oper_lag", "dl_lag", "size_lag")),     # Tabela 8: EBIT/ativo
         M("lucro_PL_niveis", d, c("ll_bi_lag", "pl_bi_lag"), "mcap_bi"),       # em níveis (Ohlson, 1995)
         M("divida_ampla", d, c("roe_lag", "dl_ampla_lag", "size_lag")),        # Tabela 8: AL ampliada
         M("sem_CEB_2022", d[!(ceb & d$ano == 2022), ]),   # Ap. C 2
         M("sem_CEB_2021_2022", d[!(ceb & d$ano %in% 2021:2022), ]),  # mercado de 2021–2022 da CEB
         M("sem_transicoes", d[!transicoes, ]),            # 69 linhas (Light 2023 já ausente)
         M("contemporaneo", cont, c("roe_atual", "dl_atual", "size_atual")),   # Ap. C 3
         M("defasado_amostra_contemporanea", cont),        # principal nas mesmas 73 linhas
         M("ROE_media3", d, c("roe_media3", "dl_lag", "size_lag")),  # Ap. C 3: média de três anos
         M("defasado_amostra_media3", d[!is.na(d$roe_media3), ]),               # mesmas 74
         M("ROE_PLmedio", d, c("roe_plmedio", "dl_lag", "size_lag")),  # Ap. C 3: PL médio
         M("defasado_amostra_PLmedio", d[!is.na(d$roe_plmedio), ]),             # mesmas 75
         M("grupos_societarios", d, grp = "grupo"),        # 12 grupos, 4.096 combinações
         M("somente_consolidadas", d[d$escopo_lag == "con", ]),                 # sem as 4 da Elektro
         M("sem_CEB_2020_2022", d[!(ceb & d$ano %in% 2020:2022), ])),          # diagnóstico extra
    lapply(c(2020, 2021, 2023, 2024, 2025), function(a) M(paste0("sem_CEB_", a), d[!(ceb & d$ano == a), ])),  # retirada de um ano da CEB por vez
    list(M("ROA_sem_CEB", d[!ceb, ], VROA)))               # diagnóstico extra
}

estimar_todos <- function(d, h, fin, comp, saida) {       # roda o catálogo e grava as saídas
  V <- FUNDAMENTOS                                            # ROE, AL e PORTE
  d <- painel_completo(d, fin, comp)                       # variáveis alternativas
  gravar(d, file.path(saida, "painel_completo.csv"))          # painel com todas as variáveis
  cont <- painel_contemporaneo(d, fin)                     # 73 linhas
  res <- lapply(catalogo_modelos(d, h, cont), function(m) {                  # 44 modelos
    r <- estimar(m$dados, m$nome, m$vars, m$dep, m$grp)    # CR1, WCR e DK
    cat(sprintf("  %-32s N=%3d G=%2d K=%2d\n", m$nome, r$modelo$N, r$modelo$G, r$modelo$K))   # acompanhamento
    r                                                         # resultado do modelo
  })
  modelos <- do.call(rbind, lapply(res, `[[`, "modelo"))   # N, G, K e R² de cada modelo
  coefs <- do.call(rbind, lapply(res, `[[`, "coefs"))      # coeficientes, CR1, WCR e DK
  gravar(modelos, file.path(saida, "modelos.csv"))            # N, G, K e R²
  gravar(coefs, file.path(saida, "coeficientes.csv"))         # coeficientes, CR1, WCR e DK

  pr <- coefs[coefs$modelo == "principal", ]               # três hipóteses do principal
  gravar(data.frame(variavel = pr$variavel, coef = pr$coef, p_WCR = pr$p_WCR, p_Holm = holm(pr$p_WCR)),  # grava holm.csv
         file.path(saida, "holm.csv"))                     # 0,0077 ; 0,0259 ; 0,0122

  base <- res[[1]]                                         # modelo principal
  vf <- vif_intra(base$F, base$X[, base$pos])              # 1,02 ; 1,36 ; 1,35
  vf_pl <- vif_intra(matriz_efeitos_fixos(d), as.matrix(d[, c(V, "lnpl_lag")]))   # com ln(PL)
  writeLines(para_json(list(VIF_intra = setNames(as.list(vf$vif), V), correlacao_intra = unname(vf$corr),  # grava diagnosticos.json
                            VIF_intra_controle_PL = setNames(as.list(vf_pl$vif), c(V, "lnpl_lag")),  # (continuação)
                            aplicacoes_ausentes = sum(is.na(d$aplicacoes)))), file.path(saida, "diagnosticos.json"))  # nenhuma das 76 sem a conta 1.01.02

  X <- base$X; P <- base$P; e <- base$e                    # matrizes do principal
  alav <- rowSums(X * t(P))                                # h_ii: alavancagem estatística
  inf <- base$dados[, c("ticker", "ano", "roe_lag", "roe_lag_bruto")]       # identificação
  inf$residuo <- e; inf$alavancagem_hat <- alav               # resíduo e alavancagem estatística
  for (i in seq_along(V)) {                                # cada fundamento
    j <- base$pos[i]                                          # posição do fundamento
    inf[[paste0("fracao_variacao_", V[i])]] <- fracao_fwl(X, j)             # de onde vem a informação
    inf[[paste0("delta_exclusao_", V[i])]] <- -P[j, ] * e / (1 - alav)      # mudança ao retirar a linha
  }
  gravar(inf, file.path(saida, "influencia_observacoes.csv"))  # grava por observação
  fr <- grep("^fracao_", names(inf), value = TRUE)            # colunas de fração
  ve <- aggregate(inf[, fr], list(ticker = inf$ticker), sum)                # soma por empresa
  gravar(ve[order(ve$ticker, method = "radix"), ], file.path(saida, "variacao_por_empresa.csv"))  # grava por empresa (CEB = 54,55% no ROE)
  invisible(list(modelos = modelos, coefs = coefs))           # resumos e coeficientes
}
