# =============================================================================
# valores.R — Uma chave para cada número do TCC
# =============================================================================
# Cada número citado no TCC tem uma chave textual, usada na conferência
# (dados/documentos/valores_publicados_tcc.csv) e no relatório ({chave;decimais;tipo}).
# A gramática está documentada em python/tcc/valores.py e no README; esta é a
# mesma regra, em R.
# =============================================================================

.res <- new.env()                                          # resultados carregados uma vez (cache)

carregar_resultados <- function(saida = RESULTADOS) {      # lê as tabelas usadas pelas chaves
  .res$coef <- ler(file.path(saida, "coeficientes.csv"))   # coeficientes
  .res$mod <- ler(file.path(saida, "modelos.csv")); rownames(.res$mod) <- .res$mod$modelo   # modelos
  .res$d <- ler(file.path(saida, "painel_principal.csv"))  # painel principal
  .res$h <- ler(file.path(saida, "painel_historico.csv"))  # painel histórico
  .res$pc <- ler(file.path(saida, "painel_completo.csv"))  # painel com variáveis alternativas
  .res$inf <- ler(file.path(saida, "influencia_observacoes.csv"))   # frações por observação
  .res$ve <- ler(file.path(saida, "variacao_por_empresa.csv"))      # frações por empresa
  .res$hl <- ler(file.path(saida, "holm.csv"))             # Holm
  .res$fun <- sapply(c("combinacoes", "capitalizacao_conciliada", "tres_fundamentos_validos", "minimo_quatro_anos"),  # funil
                     function(k) json_num(file.path(saida, "funil.json"), k))                 # funil
  .res$c7 <- sapply(c("rentabilidade", "alavancagem", "porte"),  # contagens da Tabela 7
                    function(k) json_num(file.path(saida, "tabelas_tcc", "tabela_7_contagem.json"), k))   # 12/13/15
  base <- estimar(.res$d, "principal", wcr = FALSE, dk = FALSE)                               # para o VIF
  .res$vif <- setNames(vif_intra(base$F, base$X[, base$pos])$vif, FUNDAMENTOS)  # VIF intra
  invisible(TRUE)                                             # carregado
}

valor <- function(chave) {                                 # chave → valor (número ou texto)
  k <- strsplit(chave, "|", fixed = TRUE)[[1]]             # campos da chave
  C <- function(m, v, col) .res$coef[.res$coef$modelo == m & .res$coef$variavel == v, col]  # acesso por modelo e variável
  if (k[1] %in% c("coef", "se_CR1", "p_CR1", "p_WCR", "p_DK1", "p_DK2", "IC_inf", "IC_sup", "excedencias", "combinacoes"))  # colunas de coeficientes.csv
    return(C(k[2], k[3], k[1]))                            # coluna de coeficientes.csv
  if (k[1] == "mod") return(.res$mod[k[3], k[2]])          # campo de modelos.csv
  if (k[1] == "ngk") return(paste(.res$mod[k[2], "N"], .res$mod[k[2], "G"], .res$mod[k[2], "K"], sep = "/"))   # "76/14/22"
  if (k[1] == "holm") return(.res$hl$p_Holm[.res$hl$variavel == k[2]])       # p ajustado
  if (k[1] == "desc") {                                    # Tabela 4
    d <- .res$d                                               # painel principal
    s <- switch(k[3], mcap_bi = d$mcap / 1e9, ln_mcap = d$ln_mcap, roe_pct = d$roe_lag * 100, dl_lag = d$dl_lag, size_lag = d$size_lag)  # série escolhida
    return(switch(k[2], media = mean(s), dp = sd(s), min = min(s), mediana = median(s), max = max(s)))  # estatística (desvio amostral)
  }
  if (k[1] == "vif") return(.res$vif[[k[2]]])              # VIF intra
  if (k[1] == "fwl") return(100 * .res$ve$fracao_variacao_roe_lag[.res$ve$ticker == k[2]])   # % por empresa
  if (k[1] == "fwl_obs") return(100 * .res$inf$fracao_variacao_roe_lag[.res$inf$ticker == k[2] & .res$inf$ano == as.integer(k[3])])  # % de uma observação (CEB 2022 = 31,38)
  if (k[1] == "efeito") {                                  # eq. (8), em %
    b <- C("principal", k[2], "coef")                         # coeficiente do principal
    return(100 * switch(k[2], roe_lag = exp(b * .1) - 1, dl_lag = exp(b) - 1, size_lag = 1.1^b - 1))  # eq. (8)
  }
  if (k[1] == "media_bruta") return(mean(.res$pc[[k[2]]])) # média sem winsorização
  if (k[1] == "funil") return(.res$fun[[k[2]]])            # 138, 90, 84, 76
  if (k[1] == "contagem") return(.res$c7[[k[2]]])          # 12, 13, 15
  if (k[1] == "cobertura") {                               # Tabela 1
    p <- if (k[2] == "principal") .res$d else .res$h          # painel escolhido
    return(if (k[3] == "total") nrow(p) else sum(p$ano == as.integer(k[3])))  # N ou empresas do ano
  }
  stop("chave desconhecida: ", chave)                         # erro explícito
}

formatar <- function(x, dec, tipo) {                       # formato do TCC
  if (tipo == "ngk") return(x)                             # texto pronto
  if (tipo == "int") return(as.character(as.integer(round(x))))            # inteiro
  if (tipo %in% c("p", "p_estrela") && x < 1e-4) return("< 0,0001")          # p muito pequeno
  if (tipo == "abs") x <- abs(x)                           # ex.: "6,16% menos"
  s <- gsub("-", "−", sub(".", ",", sprintf(paste0("%.", as.integer(dec), "f"), x), fixed = TRUE), fixed = TRUE)   # vírgula e −
  if (tipo == "p_estrela" && x < NIVEL) paste0(s, "*") else s                 # asterisco da Tabela 7
}
