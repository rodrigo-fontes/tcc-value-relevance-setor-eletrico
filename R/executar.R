# =============================================================================
# executar.R — Roda a reprodução completa do TCC em R
# =============================================================================
# Uso (qualquer uma das formas):
#   Terminal, na raiz do repositório:   Rscript R/executar.R
#   RStudio: abra este arquivo e clique em "Source"
#   Console do R:  source("caminho/para/tcc-value-relevance-setor-eletrico/R/executar.R")
#
# Etapas:
#   1  construir a base   capitalização, contas, fundamentos e painéis   (capitalizacao.R, contabil.R, painel.R)
#   2  estimar            modelo principal e 43 especificações          (especificacoes.R, estimacao.R)
#   3  tabelas            todas as tabelas do TCC e Figura 1             (tabelas.R)
#   4  conferir           pacote original, fixest e texto do TCC         (conferencia.R)
#   5  relatório          PDF explicado                                  (relatorio.R)
#
# Só R base (fixest é opcional, usado apenas na conferência). O andamento fica em
# resultados/r/log_execucao.txt. Uma diferença na conferência não impede o relatório;
# uma falha nas etapas 1 a 3, sim.
# =============================================================================

if (!l10n_info()$`UTF-8`) invisible(suppressWarnings(Sys.setlocale("LC_CTYPE", "C.UTF-8")))   # lê os módulos em UTF-8

RAIZ <- local({                                            # pasta do repositório (Rscript, source() ou RStudio)
  a <- gsub("~+~", " ", sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)), fixed = TRUE)   # Rscript
  if (!length(a)) a <- tryCatch(sys.frame(1)$ofile, error = function(e) NULL)    # source()
  r <- if (length(a) && !is.null(a)) dirname(dirname(normalizePath(a[1]))) else getwd()   # R/executar.R → raiz
  if (!file.exists(file.path(r, "R", "config.R")) && file.exists(file.path(r, "..", "R", "config.R")))   # rodando de dentro de R/
    r <- normalizePath(file.path(r, ".."))                 # sobe para a raiz
  if (!file.exists(file.path(r, "R", "config.R"))) stop("Não encontrei R/config.R em ", r, ". Rode a partir da raiz do repositório.")  # confere a estrutura
  r                                                        # raiz do repositório
})
for (m in c("config", "entradas", "capitalizacao", "contabil", "painel", "estimacao",   # carrega os módulos,
            "especificacoes", "tabelas", "valores", "conferencia", "relatorio"))        # na ordem de dependência
  source(file.path(RAIZ, "R", paste0(m, ".R")), encoding = "UTF-8")  # carrega o módulo
dir.create(RESULTADOS, recursive = TRUE, showWarnings = FALSE)               # cria resultados/r/
log_arq <- file.path(RESULTADOS, "log_execucao.txt")       # registro da execução
sink(log_arq, split = TRUE)                                # console e arquivo ao mesmo tempo
cat("R", R.version$major, ".", R.version$minor, "—", R.version$platform, "— pasta:", RAIZ, "\n", sep = " ")  # versão do R e pasta

etapa_1 <- function() {                                    # base empresa-ano
  d <- carregar_entradas()                                 # extratos congelados
  r <- calcular_capitalizacao(d)                           # eq. (1)
  f <- montar_financeiro(d)                                # eqs. (3)–(6)
  dec <- decisoes_amostra(r$cap, f$fin)                    # t com fundamentos de t−1
  for (rotulo in c("principal", "historico")) {            # dois painéis
    z <- montar_painel(dec, rotulo)                        # filtros e winsorização
    gravar(z, file.path(RESULTADOS, paste0("painel_", rotulo, ".csv")))  # grava o painel
    dec[[paste0("incluido_", rotulo)]] <- paste(dec$ticker, dec$ano) %in% paste(z$ticker, z$ano)   # marca as incluídas
    cat(sprintf("  painel %s: %d observações, %d empresas\n", rotulo, nrow(z), length(unique(z$ticker))))  # acompanhamento
  }
  fun <- funil_amostra(dec)                                # 138 → 90 → 84 → 76
  writeLines(para_json(fun), file.path(RESULTADOS, "funil.json"))  # grava funil.json
  cat("  funil:", unlist(fun), "\n")                          # acompanhamento
  gravar(r$cap, file.path(RESULTADOS, "capitalizacao.csv"))   # grava capitalizacao.csv
  gravar(r$comp, file.path(RESULTADOS, "componentes_capitalizacao.csv"))  # grava componentes
  gravar(f$fin, file.path(RESULTADOS, "financeiro.csv"))      # grava financeiro.csv
  gravar(f$correcoes, file.path(RESULTADOS, "correcoes_lucro.csv"))  # grava correcoes_lucro.csv
  gravar(dec, file.path(RESULTADOS, "decisoes_amostra.csv"))  # grava decisoes_amostra.csv
}
etapa_2 <- function() estimar_todos(ler(file.path(RESULTADOS, "painel_principal.csv")),        # 44 modelos
                                    ler(file.path(RESULTADOS, "painel_historico.csv")),  # (continuação)
                                    ler(file.path(RESULTADOS, "financeiro.csv")),  # (continuação)
                                    ler(file.path(RESULTADOS, "componentes_capitalizacao.csv")), RESULTADOS)  # (fim)
etapa_3 <- function() cat("  Tabela 7: linhas significativas (rentabilidade, alavancagem, porte):", gerar_tabelas(RESULTADOS), "\n")  # tabelas e contagens
etapa_4 <- function() conferir(RESULTADOS)                 # TRUE se tudo coincidir
etapa_5 <- function() gerar_relatorio()                    # PDF

etapas <- list("Construir a base" = etapa_1, "Estimar os modelos" = etapa_2, "Tabelas do TCC" = etapa_3,  # as cinco etapas
               "Conferir" = etapa_4, "Relatório em PDF" = etapa_5)  # (continuação)
situacao <- c()                                            # resultado de cada etapa
for (i in seq_along(etapas)) {                             # executa em ordem
  nome <- names(etapas)[i]; t0 <- Sys.time()                  # nome e início
  cat(sprintf("\n===== Etapa %d: %s =====\n", i, nome))       # título
  r <- tryCatch(etapas[[i]](), error = function(e) { cat("  ERRO:", conditionMessage(e), "\n"); structure(FALSE, erro = TRUE) })  # executa; erro vira FALSE marcado
  situacao[nome] <- if (isTRUE(attr(r, "erro"))) "FALHOU" else if (identical(r, FALSE)) "diferenças" else "ok"  # ok, diferenças ou FALHOU
  cat(sprintf("  (%.1f s)\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))  # tempo da etapa
  if (situacao[nome] == "FALHOU" && i <= 3) break          # sem base, modelos ou tabelas não há como continuar
}
cat("\n===== Resumo =====\n")                                 # resumo final
for (n in names(situacao)) cat(format(n, width = 22), situacao[[n]], "\n")   # format() alinha com acentos
pdf_arq <- file.path(RESULTADOS, "relatorio_reproducao.pdf")  # caminho do PDF
if (identical(unname(situacao["Relatório em PDF"]), "ok")) cat("\nRelatório gerado em:", normalizePath(pdf_arq), "\n") else  # mostra onde está o relatório
  cat("\nO relatório não foi gerado. Veja", normalizePath(log_arq, mustWork = FALSE), "\n")  # ou onde está o log
sink()                                                     # fecha o log
