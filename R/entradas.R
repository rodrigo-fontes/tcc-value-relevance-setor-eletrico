# =============================================================================
# entradas.R — Leitura dos extratos congelados
# =============================================================================
# Todos os arquivos de dados/ são lidos aqui, uma vez. Nenhuma etapa acessa a
# internet: os arquivos brutos estão identificados por SHA-256 em
# dados/fontes.json e dados/b3/manifesto_precos.json.
#
# Fontes (TCC, "Fontes de dados"): CVM (2026a) DFP; CVM (2026b) FRE; B3 (2026) COTAHIST.
# Equivale a python/tcc/entradas.py.
# =============================================================================

carregar_entradas <- function() {                          # devolve uma lista de data.frames
  cvm <- file.path(DADOS, "cvm")                           # subpasta com os extratos da CVM
  d <- list()                                              # lista de saída
  d$universo    <- ler(file.path(cvm, "universo_identificado.csv"))                 # 23 emissoras
  d$cap_dfp     <- ler(file.path(cvm, "capital_dfp.csv"))                           # ações emitidas e em tesouraria (DFP)
  d$cap_fre     <- ler(file.path(cvm, "capital_social.csv"))                        # capital social (FRE)
  d$classes_fre <- ler(file.path(cvm, "capital_social_classe_acao.csv"))            # preferenciais por subclasse
  d$eventos     <- ler(file.path(cvm, "capital_social_desdobramento.csv"))          # desdobramentos e grupamentos
  d$tesouraria  <- ler(file.path(cvm, "valor_mobiliario_tesouraria_movimentacao.csv"))   # tesouraria (FRE)
  d$tesouraria$ano_saldo <- as.integer(substr(d$tesouraria$Data_Fim_Exercicio_Social, 1, 4))   # ano do saldo final
  d$contas      <- ler(file.path(cvm, "contas_cvm.csv"), colClasses = c(CD_CONTA = "character"))   # 11 contas, em reais
  d$precos      <- ler(file.path(DADOS, "b3", "precos_dezembro_2010_2025.csv"))     # último negócio de dezembro
  d$cpfl        <- ler(file.path(DADOS, "documentos", "capital_cpfl_documentado.csv"))   # CPFL: DFs originais (6-K)
  d                                                        # devolve a lista
}

lucro_individual <- function(ano) {                        # DRE individual (conta 3.11) de um exercício
  arq <- file.path(DADOS, "cvm_complementar", sprintf("lucro_individual_%d.csv", ano))   # 2021–2024
  if (file.exists(arq)) ler(arq) else NULL                 # ausência = não há como conferir
}

aplicacoes_financeiras <- function() {                     # conta 1.01.02, última versão, em reais
  arqs <- sort(list.files(file.path(DADOS, "cvm_complementar"), "^complementos_.*\\.csv$", full.names = TRUE))  # complementos_2019.csv … complementos_2024.csv
  do.call(rbind, lapply(arqs, function(arq) {              # um data.frame por ano, empilhados
    a <- ler(arq, colClasses = c(CD_CONTA = "character"))  # códigos de conta como texto
    a$ano <- as.integer(substr(a$DT_REFER, 1, 4))          # exercício de referência
    a <- a[a$CD_CONTA == "1.01.02" & a$demonstracao == "BPA", ]                     # aplicações financeiras do ativo
    a <- a[order(a$VERSAO), ]                              # versões em ordem crescente
    a <- a[!duplicated(a[, c("CD_CVM", "ano", "escopo", "CD_CONTA")], fromLast = TRUE), ]   # fica a última versão
    a$aplicacoes <- a$VL_CONTA * c(MIL = 1000, UNIDADE = 1)[a$ESCALA_MOEDA]          # converte para reais
    a[, c("CD_CVM", "ano", "escopo", "aplicacoes")]        # só as colunas usadas
  }))
}
