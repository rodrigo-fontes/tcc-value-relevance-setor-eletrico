# =============================================================================
# painel.R — Defasagem, elegibilidade e painéis
# =============================================================================
# Regras, na ordem (TCC, "Seleção da amostra" e "Fundamentos contábeis e defasagem"):
#   1. Capitalização de dezembro de t ligada aos fundamentos do exercício t−1.
#   2. Capitalização conciliada e os três fundamentos válidos; nada é preenchido.
#   3. Pelo menos quatro exercícios por empresa (efeito fixo usa a variação interna;
#      Wooldridge, 2019; Hsiao, 2022).
#   4. Ano com uma só empresa é excluído (2010–2011 no histórico).
#   5. ROE e alavancagem winsorizados nos percentis 1 e 99 de cada painel; porte e
#      capitalização não. Os valores originais ficam em *_bruto.
# Resultado: 138 → 90 → 84 → 76 observações (14 empresas); histórico com 97 (15 empresas).
# Equivale a python/tcc/painel.py.
# =============================================================================

winsorizar <- function(x) {                                # limita aos percentis 1 e 99 da própria amostra
  q <- quantile(x, PERCENTIS_WINSOR, na.rm = TRUE, type = 7, names = FALSE)   # tipo 7 (Hyndman e Fan, 1996) = pandas
  pmin(pmax(x, q[1]), q[2])                                # substitui os extremos pelos limites
}

decisoes_amostra <- function(cap, fin) {                   # empresa-ano com fundamentos de t−1
  k <- match(paste(cap$ticker, cap$ano - 1), paste(fin$ticker, fin$ano))   # exercício anterior
  dec <- cap                                               # mantém todas as linhas
  dec$roe_lag <- fin$roe[k]; dec$dl_lag <- fin$dl[k]       # ROE e AL de t−1
  dec$size_lag <- fin$size[k]; dec$escopo_lag <- fin$escopo[k]                 # PORTE e escopo de t−1
  dec$ln_mcap <- log(dec$mcap)                             # eq. (2): y = ln(VM)
  dec$elegivel_contabil <- complete.cases(dec[, FUNDAMENTOS])                  # os três fundamentos existem
  dec                                                         # todas as empresas-ano
}

montar_painel <- function(dec, rotulo) {                   # 'principal' (2020–2025) ou 'historico' (2010–2025)
  inicio <- if (rotulo == "principal") ANO_INICIO_PRINCIPAL else ANO_INICIO_HISTORICO  # 2020 ou 2010
  z <- dec[dec$ano >= inicio & dec$status == "ok" & dec$elegivel_contabil, ]   # regra 2
  n_emp <- table(z$ticker)                                 # exercícios por empresa
  z <- z[z$ticker %in% names(n_emp)[n_emp >= MIN_EXERCICIOS], ]                # regra 3
  n_ano <- table(z$ano)                                    # empresas por ano
  z <- z[z$ano %in% as.integer(names(n_ano)[n_ano >= MIN_EMPRESAS_ANO]), ]     # regra 4
  z <- z[order(z$ticker, z$ano, method = "radix"), ]; rownames(z) <- NULL      # ordem estável
  for (v in FUNDAMENTOS[1:2]) {                            # regra 5: ROE e AL
    z[[paste0(v, "_bruto")]] <- z[[v]]                     # guarda o valor original
    z[[v]] <- winsorizar(z[[v]])                           # limites deste painel
  }
  z                                                           # painel final
}

funil_amostra <- function(dec) {                           # contagens do funil (23 emissoras × 6 anos)
  j <- dec[dec$ano >= ANO_INICIO_PRINCIPAL & dec$ano <= ANO_FIM, ]             # 2020–2025
  list(combinacoes = nrow(j),                              # 138
       capitalizacao_conciliada = sum(j$status == "ok"),   # 90
       tres_fundamentos_validos = sum(j$status == "ok" & j$elegivel_contabil),   # 84
       minimo_quatro_anos = sum(j$incluido_principal))     # 76
}
