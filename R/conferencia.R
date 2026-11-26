# =============================================================================
# conferencia.R — Três conferências independentes
# =============================================================================
#   A. resultados/ × referencia/ (pacote original, set/2026): tolerância 10⁻⁸ e contagens do WCR exatas
#   B. resultados/ × fixest (efeitos fixos de empresa e ano, cluster por empresa) — opcional
#   C. resultados/ × os 498 valores impressos no TCC (mesmas casas decimais) e listas do Apêndice A
# Equivale a python/tcc/conferencia.py (que usa statsmodels e linearmodels no item B).
# =============================================================================

conferir <- function(saida = RESULTADOS) {                 # roda A, B e C; devolve TRUE se tudo coincidir
  falhas <- c()                                            # rótulos que falharam
  confere <- function(rotulo, a, b, tol = 1e-8) {          # comparação numérica
    a <- as.numeric(unlist(a)); b <- as.numeric(unlist(b)) # vetores
    dif <- if (length(a)) max(abs(a - b) / pmax(1, abs(b)), na.rm = TRUE) else 0   # diferença relativa máxima
    ok <- length(a) == length(b) && identical(is.na(a), is.na(b)) && dif <= tol   # mesmos ausentes e dentro da tolerância
    cat(sprintf("  [%s] %s diferença máx. %.1e\n", if (ok) "ok" else "FALHA", format(rotulo, width = 60), dif))   # format() conta caracteres, não bytes
    if (!ok) falhas <<- c(falhas, rotulo)                  # registra
  }

  cat("A. Resultados × pacote original (referencia/)\n")      # título
  pares <- c(capitalizacao_final = "capitalizacao", componentes_final = "componentes_capitalizacao",  # arquivos da construção
             financeiro_final = "financeiro", decisoes_amostra = "decisoes_amostra",  # (continuação)
             painel_principal = "painel_principal", painel_historico = "painel_historico")   # arquivos da construção
  for (r in names(pares)) {                                # cada arquivo
    a <- ler(file.path(saida, paste0(pares[[r]], ".csv"))); b <- ler(file.path(REFERENCIA, paste0(r, ".csv")))  # calculado e referência
    num <- names(b)[sapply(b, is.numeric) & names(b) %in% names(a)]          # colunas numéricas em comum
    confere(sprintf("%s (%d linhas)", pares[[r]], nrow(b)), a[, num], b[, num], 1e-9)  # compara
  }
  coef <- ler(file.path(saida, "coeficientes.csv"))        # coeficientes calculados
  ref <- ler(file.path(REFERENCIA, "estimativas_integral.csv"))              # 37 modelos com CR1 e WCR
  j <- merge(ref, coef, by = c("modelo", "variavel"), suffixes = c("_ref", ""))   # pareia
  stopifnot(nrow(j) == nrow(ref))                          # todos os modelos de referência existem
  for (c in c("coef", "se_CR1", "p_CR1", "IC_inf", "IC_sup", "p_WCR"))  # cada estatística
    confere(sprintf("%s (%d modelos, %d coeficientes)", c, length(unique(j$modelo)), nrow(j)), j[[c]], j[[paste0(c, "_ref")]])  # compara
  confere("excedências do WCR (contagens exatas)", j$excedencias, j$excedencias_ref, 0)   # tolerância zero
  for (arq in c("estimativas_revisao", "estimativas_finais")) {              # Driscoll–Kraay
    r <- ler(file.path(REFERENCIA, paste0(arq, ".csv")))      # estimativas com DK
    for (bw in DEFASAGENS_DK) {                               # 1 e 2 defasagens
      x <- merge(r[r$metodo == paste0("DK", bw), ], coef, by = c("modelo", "variavel"))  # linhas DK
      confere(sprintf("Driscoll–Kraay %d: erro-padrão (%s)", bw, arq), x[[paste0("se_DK", bw)]], x$se)  # compara
    }
  }
  mod <- ler(file.path(saida, "modelos.csv")); rownames(mod) <- mod$modelo  # modelos calculados
  mi <- ler(file.path(REFERENCIA, "modelos_integral.csv"))                   # N, G, K e R² de referência
  for (c in c("N", "G", "K", "R2_intra", "R2_parcial")) confere(paste(c, "(37 modelos)"), mod[mi$modelo, c], mi[[c]])  # compara N, G, K e R²
  hr <- ler(file.path(REFERENCIA, "holm_principal.csv")); hp <- ler(file.path(saida, "holm.csv"))  # Holm: referência e calculado
  confere("p de Holm", hp$p_Holm[match(hr$variavel, hp$variavel)], hr$p_Holm)  # compara
  vr <- ler(file.path(REFERENCIA, "variacao_por_empresa.csv")); vp <- ler(file.path(saida, "variacao_por_empresa.csv"))  # FWL: referência e calculado
  confere("fração FWL por empresa", vp[match(vr$ticker, vp$ticker), -1], vr[, -1])  # compara

  cat("\nB. Resultados × fixest\n")                           # título
  if (requireNamespace("fixest", quietly = TRUE)) {        # conferência opcional: um erro aqui não interrompe nada
    tryCatch({                                                # erros aqui não interrompem
      d <- ler(file.path(saida, "painel_completo.csv"))       # painel com o grupo societário
      ajuste <- tryCatch(fixest::ssc(K.adj = TRUE, K.fixef = "full", G.adj = TRUE, t.df = "min"),   # fixest >= 0.13
                         error = function(e) fixest::ssc(adj = TRUE, fixef.K = "full", cluster.adj = TRUE, t.df = "min"))   # anteriores
      pc <- coef[coef$modelo == "principal", ]                # principal
      fx <- fixest::feols(ln_mcap ~ roe_lag + dl_lag + size_lag | ticker + ano, data = d, cluster = ~ticker, ssc = ajuste)  # efeitos fixos de empresa e ano, cluster por empresa
      confere("fixest: coeficientes", coef(fx)[pc$variavel], pc$coef)  # compara
      confere("fixest: erro-padrão CR1", fixest::se(fx)[pc$variavel], pc$se_CR1, 1e-6)        # fixest centra com tolerância própria
      confere("fixest: p CR1 com t(13)", fixest::pvalue(fx)[pc$variavel], pc$p_CR1, 1e-6)  # compara
      fg <- fixest::feols(ln_mcap ~ roe_lag + dl_lag + size_lag | ticker + ano, data = d, cluster = ~grupo, ssc = ajuste)  # cluster por grupo societário (12)
      pg <- coef[coef$modelo == "grupos_societarios", ]       # modelo de grupos
      confere("fixest: erro-padrão com 12 grupos societários", fixest::se(fg)[pg$variavel], pg$se_CR1, 1e-6)  # compara
    }, error = function(e) cat("  conferência com fixest não executada:", conditionMessage(e), "\n"))  # mensagem, sem interromper
  } else cat("  fixest não instalado: conferência B omitida (install.packages('fixest'))\n")  # fixest ausente

  cat("\nC. Resultados × valores publicados no TCC\n")        # título
  carregar_resultados(saida)                               # tabelas usadas pelas chaves
  pub <- read.csv(file.path(DADOS, "documentos", "valores_publicados_tcc.csv"), colClasses = "character",  # valores publicados, como texto
                  encoding = "UTF-8", check.names = FALSE) # valores publicados, como texto
  pub$calculado <- mapply(function(c, dc, t) formatar(valor(c), dc, t), pub$chave, pub$decimais, pub$tipo)   # recalcula
  pub$confere <- pub$calculado == pub$publicado            # comparação do texto formatado
  gravar(pub, file.path(saida, "conferencia_tcc.csv"))        # grava conferencia_tcc.csv
  for (t in unique(pub$tabela)) {                          # resumo por tabela
    g <- pub[pub$tabela == t, ]                               # valores da tabela
    ok <- all(g$confere)                                      # todos coincidem?
    cat(sprintf("  [%s] %s %d de %d valores\n", if (ok) "ok" else "FALHA", format(t, width = 42), sum(g$confere), nrow(g)))  # linha do relatório
    if (!ok) { falhas <- c(falhas, t); print(g[!g$confere, c("linha", "item", "publicado", "calculado")]) }  # mostra as divergências
  }
  # Apêndice A: as 14 companhias do painel e as 9 fora dele são exatamente as do TCC, e cada uma
  # das 9 tem menos de quatro exercícios elegíveis (o motivo de ficar fora)
  el <- elegibilidade(saida)                               # 23 emissoras
  dentro <- el$ticker[el$no_painel > 0]; fora <- el$ticker[el$no_painel == 0]   # dentro e fora do painel
  tcc_dentro <- ler(file.path(DADOS, "documentos", "caracterizacao_empresas.csv"))$codigo  # Apêndice A, Tabela 1
  tcc_fora <- ler(file.path(DADOS, "documentos", "companhias_fora_painel_tcc.csv"))$ticker  # Apêndice A, Tabela 2
  ok <- setequal(dentro, tcc_dentro) && setequal(fora, tcc_fora) && all(el[fora, "elegiveis"] < MIN_EXERCICIOS)  # três testes
  cat(sprintf("  [%s] %s %d no painel e %d fora, como no TCC\n", if (ok) "ok" else "FALHA",  # linha do relatório
              format("Apêndice A: listas de empresas", width = 42), length(dentro), length(fora)))  # (continuação)
  if (!ok) falhas <- c(falhas, "Apêndice A: listas de empresas")  # registra
  cat("\n", if (!length(falhas)) "TUDO CONFERIDO." else paste(length(falhas), "FALHA(S):", paste(falhas, collapse = "; ")), "\n")  # resultado final
  !length(falhas)                                          # TRUE se tudo coincidir
}
