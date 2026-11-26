# =============================================================================
# tabelas.R — Tabelas e Figura 1 no formato do TCC
# =============================================================================
# Um CSV por tabela do trabalho em resultados/tabelas_tcc/, com o arredondamento
# do texto (ponto decimal; o relatório converte para vírgula). "*" = p WCR < 0,05
# antes do arredondamento. Mapa arquivo → tabela no cabeçalho de python/tcc/tabelas.py.
# Equivale àquele módulo; os CSVs gerados são idênticos.
# =============================================================================

NOMES_FUND <- c(roe_lag = "ROE defasado", dl_lag = "Alavancagem defasada", size_lag = "Porte defasado")  # rótulos dos fundamentos
LINHAS_T7 <- c("Principal" = "principal", "Sem winsorização" = "sem_winsor", "Sem CEB" = "excluir_CEBR3",   # 18 linhas
               "Sem Auren" = "excluir_AURE3", "Sem Light" = "excluir_LIGT3", "Sem Taesa" = "excluir_TAEE3",  # da Tabela 7,
               "Sem Elektro e Taesa" = "sem_EKTR_TAEE", "Balanceado" = "balanceado",                       # na ordem
               "Negócios desde 20 dez." = "cotacoes_desde_dia20", "Histórico" = "historico",               # do texto
               "Histórico: mesmas 14" = "historico_mesmas_empresas", "+ ln(PL)" = "controle_PL",  # (continuação)
               "ROA líquido" = "ROA", "ROA operacional" = "ROA_operacional", "Dívida ampliada" = "divida_ampla",  # (continuação)
               "Sem CEB-2022" = "sem_CEB_2022", "CEB: sem 2021–22" = "sem_CEB_2021_2022", "Sem transições" = "sem_transicoes")  # (fim)
ROTULOS_T8 <- c(roe_lag = "ROE", dl_lag = "Alavancagem", size_lag = "ln(ativo)", lnpl_lag = "ln(PL)",          # rótulos
                roa_lag = "ROA líquido", roa_oper_lag = "ROA operacional", ll_bi_lag = "Lucro (R$ bi)",        # da
                pl_bi_lag = "PL (R$ bi)", dl_ampla_lag = "Alav. ampliada")                                    # Tabela 8

f4 <- function(x, n = 4) ifelse(is.na(x), "", sprintf(paste0("%.", n, "f"), x))   # n casas decimais
fp <- function(p) ifelse(p < 0.0001, "< 0.0001", f4(p))   # regra do texto do TCC para p

gerar_tabelas <- function(saida) {                         # gera todas as tabelas e a Figura 1
  tab <- file.path(saida, "tabelas_tcc"); dir.create(tab, showWarnings = FALSE)   # pasta de saída
  coef <- ler(file.path(saida, "coeficientes.csv"))        # coeficientes de todos os modelos
  mod <- ler(file.path(saida, "modelos.csv")); rownames(mod) <- mod$modelo         # resumo dos modelos
  d <- ler(file.path(saida, "painel_principal.csv"))       # 76 observações
  h <- ler(file.path(saida, "painel_historico.csv"))       # 97 observações
  C <- function(m, v, col) coef[coef$modelo == m & coef$variavel == v, col]       # acesso por modelo e variável
  ngk <- function(m) sprintf("%d/%d/%d", mod[m, "N"], mod[m, "G"], mod[m, "K"])   # "76/14/22"
  V <- FUNDAMENTOS                                            # ROE, AL e PORTE

  # Tabela 1 — empresas por ano em cada painel
  anos <- 2010:2025                                           # anos de mercado
  t1 <- data.frame(ano = as.character(anos), principal = sapply(anos, function(a) sum(d$ano == a)),  # contagem por ano
                   historico = sapply(anos, function(a) sum(h$ano == a)))  # (continuação)
  t1 <- t1[t1$principal > 0 | t1$historico > 0, ]           # só anos com alguma empresa
  t1 <- rbind(t1, data.frame(ano = c("total", "empresas"), principal = c(nrow(d), length(unique(d$ticker))),  # linhas de total
                             historico = c(nrow(h), length(unique(h$ticker)))))   # 76/97 e 14/15
  gravar(t1, file.path(tab, "tabela_1_cobertura.csv"))        # grava a Tabela 1

  # Tabela 4 — descritivas (ROE em %, VM em R$ bilhões); sd() é o desvio amostral (n−1)
  desc <- list("Valor de mercado (R$ bilhões)" = d$mcap / 1e9, "ln do valor de mercado" = d$ln_mcap,  # cinco variáveis da Tabela 4
               "ROE defasado (%)" = d$roe_lag * 100, "Alavancagem defasada (vezes)" = d$dl_lag,  # (continuação)
               "Porte defasado (ln R$)" = d$size_lag)         # (fim)
  gravar(do.call(rbind, lapply(names(desc), function(k) { v <- desc[[k]]  # uma linha por variável
    data.frame(variavel = k, media = f4(mean(v), 2), desvio_padrao = f4(sd(v), 2), minimo = f4(min(v), 2),  # média, desvio, mínimo
               mediana = f4(median(v), 2), maximo = f4(max(v), 2)) })), file.path(tab, "tabela_4_descritivas.csv"))  # mediana e máximo; grava

  # Tabela 5 — coeficiente, erro-padrão CR1, p com t(13) e IC de 95%
  gravar(do.call(rbind, lapply(V, function(v) data.frame(     # uma linha por fundamento
    fundamento = NOMES_FUND[[v]], coeficiente = f4(C("principal", v, "coef")), erro_padrao = f4(C("principal", v, "se_CR1")),  # coeficiente e erro-padrão
    p_CR1 = fp(C("principal", v, "p_CR1")), IC95_inf = f4(C("principal", v, "IC_inf")), IC95_sup = f4(C("principal", v, "IC_sup"))))),  # p e IC de 95%
    file.path(tab, "tabela_5_coeficientes.csv"))              # grava a Tabela 5

  # Tabela 6 — CR1 × WCR, com Holm e as contagens exatas do bootstrap
  hl <- ler(file.path(saida, "holm.csv"))                     # Holm
  gravar(do.call(rbind, lapply(V, function(v) data.frame(     # uma linha por fundamento
    fundamento = NOMES_FUND[[v]], p_CR1 = fp(C("principal", v, "p_CR1")), p_WCR = f4(C("principal", v, "p_WCR")),  # p CR1 e p WCR
    p_Holm = f4(hl$p_Holm[hl$variavel == v]), excedencias = C("principal", v, "excedencias"),  # Holm e excedências
    combinacoes = C("principal", v, "combinacoes")))), file.path(tab, "tabela_6_cr1_wcr_holm.csv"))  # combinações; grava a Tabela 6

  # Eq. (8): Δ%VM = 100 [exp(β Δx) − 1]; porte (log-log): 1,10^β − 1
  b <- sapply(V, function(v) C("principal", v, "coef"))       # β1, β2, β3
  gravar(data.frame(fundamento = c("ROE +10 p.p.", "Alavancagem +1 vez", "Ativo +10%"),  # eq. (8)
                    calculo = c("exp(b x 0,10) - 1", "exp(b) - 1", "1,10^b - 1"),  # fórmula de cada linha
                    efeito_pct = f4(100 * c(exp(b[["roe_lag"]] * .10) - 1, exp(b[["dl_lag"]]) - 1, 1.10^b[["size_lag"]] - 1), 2)),  # −6,16 ; −9,62 ; 5,04
         file.path(tab, "interpretacao_efeitos.csv"))       # −6,16 ; −9,62 ; 5,04

  # Tabela 7 — p WCR das 18 verificações
  estrela <- function(m, v) { p <- C(m, v, "p_WCR"); paste0(f4(p), ifelse(p < NIVEL, "*", "")) }  # p WCR com "*" se < 0,05 antes de arredondar
  t7 <- do.call(rbind, lapply(names(LINHAS_T7), function(rot) { m <- LINHAS_T7[[rot]]; vs <- coef$variavel[coef$modelo == m]  # 18 linhas
    data.frame(modelo = rot, N_G_K = ngk(m), R2_intra = f4(mod[m, "R2_intra"], 3),  # N/G/K e R² intra
               rentabilidade = estrela(m, vs[grepl("^(roe|roa)", vs)][1]),   # ROE, ou ROA nas linhas de ROA
               alavancagem = estrela(m, vs[grepl("^dl", vs)][1]),            # AL, ou AL ampliada
               porte = estrela(m, "size_lag")) }))            # p WCR do porte
  gravar(t7, file.path(tab, "tabela_7_sensibilidade.csv"))    # grava a Tabela 7
  cont <- sapply(c("rentabilidade", "alavancagem", "porte"), function(c) sum(endsWith(t7[[c]], "*")))   # 12, 13, 15
  writeLines(para_json(list(linhas = nrow(t7), significativos = as.list(cont))), file.path(tab, "tabela_7_contagem.json"))  # contagens 12/13/15

  # Tabela 8 — especificações alternativas na mesma amostra
  l8 <- c("+ ln(PL)" = "controle_PL", "ROA líquido" = "ROA", "ROA operacional" = "ROA_operacional",  # cinco especificações
          "Lucro e PL" = "lucro_PL_niveis", "Dívida ampliada" = "divida_ampla")  # (continuação)
  gravar(do.call(rbind, lapply(names(l8), function(rot) { m <- l8[[rot]]; x <- coef[coef$modelo == m, ]  # uma linha por variável do modelo
    data.frame(modelo = rot, variavel = unname(ROTULOS_T8[x$variavel]), coef = f4(x$coef), p_CR1 = fp(x$p_CR1),  # coeficiente e p CR1
               p_WCR = f4(x$p_WCR), N_G_K = ngk(m), R2_intra = f4(mod[m, "R2_intra"], 3)) })),  # p WCR, N/G/K e R²
    file.path(tab, "tabela_8_especificacoes.csv"))            # grava a Tabela 8

  # Apêndice C, Tabela 1 — retirada de cada empresa: coeficiente (erro-padrão CR1)
  emps <- sort(unique(d$ticker), method = "radix")            # 14 empresas
  gravar(do.call(rbind, lapply(emps, function(e) { m <- paste0("excluir_", e)  # uma linha por retirada
    cel <- function(v) sprintf("%.3f (%.3f)", C(m, v, "coef"), C(m, v, "se_CR1"))  # "coef (erro-padrão)"
    data.frame(retirada = e, N_G_K = ngk(m), R2_intra = f4(mod[m, "R2_intra"], 3),  # N/G/K e R² intra
               ROE = cel("roe_lag"), Alavancagem = cel("dl_lag"), Porte = cel("size_lag")) })),  # três fundamentos
    file.path(tab, "apC_tabela_1_retiradas.csv"))             # grava

  # Apêndice C, Tabela 2 — balanceado e janelas de transição (com DK1)
  l2 <- c("Balanceado" = "balanceado", "Sem CEB em 2022" = "sem_CEB_2022", "CEB: sem 2021–22" = "sem_CEB_2021_2022",  # quatro recortes
          "Sem transições" = "sem_transicoes")                # (fim)
  gravar(do.call(rbind, lapply(names(l2), function(rot) { m <- l2[[rot]]  # um bloco por recorte
    do.call(rbind, lapply(V, function(v) data.frame(modelo = rot, variavel = NOMES_FUND[[v]], coef = f4(C(m, v, "coef")),  # coeficiente
      p_CR1 = fp(C(m, v, "p_CR1")), p_WCR = f4(C(m, v, "p_WCR")), p_DK1 = fp(C(m, v, "p_DK1")),  # quatro valores de p
      N_G_K = ngk(m), R2_intra = f4(mod[m, "R2_intra"], 3)))) })), file.path(tab, "apC_tabela_2_balanceado_janelas.csv"))  # grava

  # Apêndice C, Tabela 3 — alinhamento temporal, rentabilidade e agrupamento
  l3 <- c("Contemporâneo" = "contemporaneo", "Defasado: mesmas 73" = "defasado_amostra_contemporanea",  # oito modelos
          "ROE médio: três anos" = "ROE_media3", "Defasado: mesmas 74" = "defasado_amostra_media3",  # (continuação)
          "ROE: PL médio" = "ROE_PLmedio", "Defasado: mesmas 75" = "defasado_amostra_PLmedio",  # (continuação)
          "Grupos societários" = "grupos_societarios", "Só consolidadas" = "somente_consolidadas")  # (fim)
  gravar(do.call(rbind, lapply(names(l3), function(rot) { m <- l3[[rot]]; x <- coef[coef$modelo == m, ]  # uma linha por variável
    data.frame(modelo = rot, variavel = x$variavel, coef = f4(x$coef), p_CR1 = fp(x$p_CR1), p_WCR = f4(x$p_WCR),  # coeficiente e p
               N_G_K = ngk(m), R2_intra = f4(mod[m, "R2_intra"], 3)) })), file.path(tab, "apC_tabela_3_alinhamento_agrupamento.csv"))  # grava

  # Apêndice C, Tabela 4 — Driscoll–Kraay do modelo principal
  gravar(data.frame(fundamento = unname(NOMES_FUND[V]), p_DK1 = fp(sapply(V, function(v) C("principal", v, "p_DK1"))),  # Driscoll–Kraay do principal
                    p_DK2 = fp(sapply(V, function(v) C("principal", v, "p_DK2")))), file.path(tab, "apC_tabela_4_driscoll_kraay.csv"))  # grava

  # Tabelas descritivas (texto e códigos) e as do Apêndice A
  tabelas_descritivas(saida)                                  # Tabelas 2 e 3, Apêndice A (1 e 2), Apêndice B (1)

  # Números citados no texto (R², VIF, concentração da CEB, dívida ampliada, funil)
  inf <- ler(file.path(saida, "influencia_observacoes.csv")); ve <- ler(file.path(saida, "variacao_por_empresa.csv"))  # frações por observação e por empresa
  pc <- ler(file.path(saida, "painel_completo.csv"))          # painel com dívida ampliada
  base <- estimar(d, "principal", wcr = FALSE, dk = FALSE) # só para o VIF
  vif <- vif_intra(base$F, base$X[, base$pos])$vif            # 1,02 ; 1,36 ; 1,35
  fun <- readLines(file.path(saida, "funil.json"))            # funil
  resumo <- list(R2_global = f4(mod["principal", "R2_global"]), R2_intra = f4(mod["principal", "R2_intra"]),  # 0,9711 ; 0,2130
                 R2_parcial = f4(mod["principal", "R2_parcial"]), VIF_intra = setNames(as.list(f4(vif, 2)), unname(NOMES_FUND[V])),  # 0,2896 e VIF
                 CEB_fracao_variacao_ROE_pct = f4(100 * ve$fracao_variacao_roe_lag[ve$ticker == "CEBR3"], 2),  # 54,55%
                 CEB_2022_fracao_variacao_ROE_pct = f4(100 * inf$fracao_variacao_roe_lag[inf$ticker == "CEBR3" & inf$ano == 2022], 2),  # 31,38%
                 divida_media_bruta = f4(mean(pc$dl_lag_bruto)), divida_ampliada_media_bruta = f4(mean(pc$dl_ampla_lag_bruto)))  # 2,5057 → 2,2793
  writeLines(c(sub("\n}$", ",", para_json(resumo)), paste0('  "funil": ', paste(fun, collapse = "\n  ")), "}"),  # acrescenta o funil
             file.path(tab, "diagnosticos_texto.json"))       # grava

  png(file.path(saida, "figura_1.png"), width = 6.3, height = 4.6, units = "in", res = 300)   # Figura 1 avulsa
  par(mfrow = c(1, 3), oma = c(0, 7.5, 0, 0))                 # três painéis; margem para os nomes
  for (k in 1:3) desenhar_painel_figura1(coef, d, k)          # desenha
  invisible(dev.off())                                        # fecha o PNG
  invisible(cont)                                             # contagens
}

# Por empresa, na janela do painel principal (2020–2025): anos com capitalização conciliada, anos com
# os três fundamentos de t−1, exercícios elegíveis (os dois ao mesmo tempo), anos no painel e os
# motivos de exclusão registrados (do mais ao menos frequente). Base das duas tabelas do Apêndice A.
elegibilidade <- function(saida) {                         # empresa × janela principal
  d <- ler(file.path(saida, "decisoes_amostra.csv"))       # uma linha por empresa-ano (23 emissoras)
  d <- d[d$ano >= ANO_INICIO_PRINCIPAL & d$ano <= ANO_FIM, ]  # janela 2020–2025
  d$cap_ok <- d$status == "ok"                             # capitalização conciliada
  d$fund_ok <- complete.cases(d[, FUNDAMENTOS])            # ROE, AL e PORTE de t−1 disponíveis
  motivos <- function(s) { s <- s[s != "ok"]; u <- unique(s)  # códigos de exclusão distintos (ordem de aparição)
    if (!length(u)) return("")                                # empresa sem exclusões
    paste(u[order(-vapply(u, function(x) sum(s == x), 0))], collapse = ";") }  # do mais ao menos frequente (empate: ordem de aparição)
  tk <- sort(unique(d$ticker))                             # empresas em ordem alfabética (como o groupby do pandas)
  data.frame(ticker = tk, row.names = tk,                  # uma linha por empresa
             capitalizacao = sapply(tk, function(t) sum(d$cap_ok[d$ticker == t])),  # anos com capitalização
             fundamentos = sapply(tk, function(t) sum(d$fund_ok[d$ticker == t])),  # anos com fundamentos
             elegiveis = sapply(tk, function(t) sum(d$cap_ok[d$ticker == t] & d$fund_ok[d$ticker == t])),  # os dois
             no_painel = sapply(tk, function(t) sum(verdade(as.logical(d$incluido_principal[d$ticker == t])))),  # anos no painel
             motivo = sapply(tk, function(t) motivos(d$status[d$ticker == t])))  # motivos de exclusão
}

MOTIVOS <- c(excluir_preco_classe_ausente = "sem cotação de dezembro da classe",  # P da mesma classe ausente
             excluir_capital_ambiguo_ou_ausente = "capital ambíguo ou ausente na CVM",  # Q não determinada
             excluir_tesouraria_nao_documentada = "tesouraria não documentada",  # T ausente
             excluir_subclasses_ou_tesouraria = "subclasses (PNA/PNB) ou tesouraria sem repartição",  # Q por classe indeterminada
             excluir_divergencia_tesouraria_DFP_FRE = "tesouraria divergente entre DFP e FRE",  # T inconsistente
             excluir_divergencia_tesouraria_FRE = "tesouraria ambígua no FRE",  # T inconsistente
             excluir_tesouraria_evento_posterior = "evento societário com tesouraria",  # evento desfeito + T
             excluir_quantidade_invalida = "quantidade em circulação não positiva")  # Q − T ≤ 0

# Tabelas 2 e 3 do TCC, Apêndice A (Tabelas 1 e 2) e Apêndice B (Tabela 1).
# O texto vem de config.R (o mesmo do TCC); os números e as listas de empresas vêm dos dados.
tabelas_descritivas <- function(saida) {                   # tabelas sem estimação
  tab <- file.path(saida, "tabelas_tcc")                     # pasta de saída
  gravar(ETAPAS_TCC, file.path(tab, "tabela_2_etapas.csv"))  # Tabela 2 + módulo que executa
  gravar(VARIAVEIS_TCC, file.path(tab, "tabela_3_variaveis.csv"))  # Tabela 3

  el <- elegibilidade(saida)                                 # contagens por empresa (2020–2025)
  d <- ler(file.path(saida, "painel_principal.csv"))         # 76 observações
  car <- ler(file.path(DADOS, "documentos", "caracterizacao_empresas.csv"))  # segmento e relação societária (TCC)
  gravar(data.frame(companhia = car$companhia, ticker = car$codigo,  # Apêndice A, Tabela 1
                    N = sapply(car$codigo, function(t) sum(d$ticker == t)),  # N recalculado a partir do painel
                    segmento = car$segmento_G_geracao_T_transmissao_D_distribuicao,  # segmento (documental)
                    relacao_societaria = car$relacao_societaria), file.path(tab, "apA_tabela_1_companhias.csv"))  # grava

  fora <- el[el$no_painel == 0, ]                            # emissoras sem nenhum ano no painel principal
  fora$motivos_no_codigo <- vapply(strsplit(fora$motivo, ";", fixed = TRUE),  # motivos legíveis
                                   function(m) paste(unname(MOTIVOS[m[m != ""]]), collapse = "; "), "")  # (continuação)
  tcc <- ler(file.path(DADOS, "documentos", "companhias_fora_painel_tcc.csv"))  # restrições como escritas no TCC
  fora <- merge(fora, tcc, by = "ticker", all = TRUE)        # all: uma empresa só de um lado aparece
  gravar(fora[order(fora$ticker), c("identificador", "ticker", "capitalizacao", "fundamentos", "elegiveis",  # colunas
                                    "motivos_no_codigo", "restricao_tcc")], file.path(tab, "apA_tabela_2_fora_do_painel.csv"))  # grava

  gravar(RUBRICAS, file.path(tab, "apB_tabela_1_rubricas.csv"))  # Apêndice B, Tabela 1
}

desenhar_painel_figura1 <- function(coef, d, k) {          # um painel da Figura 1 (k = 1 ROE, 2 AL, 3 PORTE)
  C <- function(m, v, col) coef[coef$modelo == m & coef$variavel == v, col]  # acesso por modelo e variável
  v <- FUNDAMENTOS[k]                                      # fundamento do painel
  emps <- sort(unique(d$ticker), method = "radix"); n <- length(emps); yy <- seq_len(n)   # uma linha por empresa
  x <- sapply(emps, function(e) C(paste0("excluir_", e), v, "coef"))         # coeficiente sem a empresa
  lo <- sapply(emps, function(e) C(paste0("excluir_", e), v, "IC_inf"))      # limite inferior CR1 95%
  hi <- sapply(emps, function(e) C(paste0("excluir_", e), v, "IC_sup"))      # limite superior
  ceb <- emps == "CEBR3"                                   # destaque da CEB
  par(mar = c(2.3, 0.3, 1.3, 0.2), mgp = c(1.3, 0.35, 0), tcl = -0.2)  # margens do painel
  plot(x, yy, xlim = range(c(lo, hi, 0)), ylim = c(n + 0.5, 0.5), type = "n", yaxt = "n", bty = "l",  # eixos, sem pontos
       xlab = "Coeficiente e IC 95%", ylab = "", cex.axis = 0.6, cex.lab = 0.62)   # eixos sem pontos
  title(c("A. ROE", "B. Alavancagem", "C. Porte")[k], adj = 0, cex.main = 0.72, font.main = 1)  # A, B ou C
  abline(v = 0, col = "grey65")                            # referência: zero
  abline(v = C("principal", v, "coef"), lty = 2, col = "grey35")             # modelo principal (tracejado)
  arrows(lo, yy, hi, yy, angle = 90, code = 3, length = 0.015, col = ifelse(ceb, "black", "grey45"))   # intervalos
  points(x, yy, pch = ifelse(ceb, 18, 16), cex = ifelse(ceb, 1.1, 0.6), col = ifelse(ceb, "black", "grey45"))   # losango = CEB
  axis(2, at = yy, labels = if (k == 1) unname(NOMES_EMPRESAS[emps]) else FALSE, las = 1, cex.axis = 0.62)   # nomes no 1º
}
