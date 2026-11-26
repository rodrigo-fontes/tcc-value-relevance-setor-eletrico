# =============================================================================
# estimacao.R — Estimação e inferência (eq. 7, Tabelas 5 e 6 e Apêndice B do TCC)
# =============================================================================
#
#   (7)  y_it = α_i + λ_t + β1·ROE_i,t−1 + β2·AL_i,t−1 + β3·PORTE_i,t−1 + ε_it
#
#   α_i: efeito fixo da empresa · λ_t: efeito fixo do ano. Mínimos quadrados com
#   indicadoras (LSDV), uma categoria de referência em cada fator (Wooldridge, 2019; Hsiao, 2022).
#
#   CR1  erro-padrão por empresa, fator G/(G−1)·(N−1)/(N−K), t(G−1) (Cameron e Miller, 2015;
#        MacKinnon, Nielsen e Webb, 2023)
#   WCR  bootstrap selvagem agrupado restrito, Rademacher por empresa, 2^G combinações
#        (Cameron, Gelbach e Miller, 2008; Roodman et al., 2019) — teste prioritário
#   Holm três hipóteses do modelo principal (Holm, 1979)
#   DK   Driscoll–Kraay, Bartlett com 1 ou 2 defasagens, N/(N−K), t(N−K) (Driscoll e Kraay, 1998;
#        Hoechle, 2007; pesos de Newey e West, 1987)
#   FWL  fração da variação identificadora (Frisch e Waugh, 1933; Lovell, 1963)
#
# Só R base. Equivale a python/tcc/estimacao.py.
# =============================================================================

matriz_efeitos_fixos <- function(a) {                      # constante + indicadoras de empresa e de ano
  unname(model.matrix(~ factor(ticker) + factor(ano), data = a))   # uma categoria omitida em cada fator
}

residualizar <- function(A, B) qr.resid(qr(A), B)          # parte de B que A não explica (FWL)

pseudo_inversa <- function(X) {                            # P = (X'X)⁻¹X' via QR: P = R⁻¹Q'
  q <- qr(X)                                               # decomposição QR
  stopifnot(q$rank == ncol(X))                             # posto completo
  P <- backsolve(qr.R(q), t(qr.Q(q)))                      # R⁻¹ Q'
  Pn <- P; Pn[q$pivot, ] <- P                              # desfaz eventual permutação de colunas
  Pn                                                          # pseudo-inversa
}

estimar <- function(dados, nome, variaveis = FUNDAMENTOS, dependente = DEPENDENTE, grupo = "ticker",  # um modelo completo
                    wcr = TRUE, dk = TRUE) {               # estima um modelo completo
  a <- dados[complete.cases(dados[, c(variaveis, dependente, grupo)]), , drop = FALSE]   # só linhas completas
  rownames(a) <- NULL                                         # renumera
  F <- matriz_efeitos_fixos(a)                             # α_i e λ_t
  X <- cbind(F, as.matrix(a[, variaveis]))                 # efeitos fixos + fundamentos
  y <- a[[dependente]]                                     # variável explicada
  N <- nrow(X); K <- ncol(X)                               # observações e parâmetros
  stopifnot(qr(X)$rank == K)                               # nenhuma coluna redundante

  P <- pseudo_inversa(X)                                   # K × N: peso de cada observação em cada coeficiente
  b <- drop(P %*% y)                                       # coeficientes
  e <- drop(y - X %*% b)                                   # resíduos
  pos <- (K - length(variaveis) + 1):K                     # posições dos fundamentos

  g <- match(a[[grupo]], unique(a[[grupo]]))               # grupo de cada observação (ordem de aparição)
  G <- max(g)                                              # 14 empresas ou 12 grupos
  fator_cr1 <- G / (G - 1) * (N - 1) / (N - K)             # correção de pequena amostra

  escore <- t(sapply(seq_len(G), function(c) P[, g == c, drop = FALSE] %*% e[g == c]))   # G × K
  se_cr1 <- sqrt(fator_cr1 * colSums(escore^2))            # erro-padrão CR1
  t_cr1 <- b / se_cr1                                      # estatística t
  p_cr1 <- 2 * pt(-abs(t_cr1), G - 1)                      # p bilateral com t(G−1)
  crit <- qt(0.975, G - 1)                                 # valor crítico do IC de 95%

  r2_global <- 1 - sum(e^2) / sum((y - mean(y))^2)         # inclui os efeitos fixos (0,9711)
  yF <- residualizar(F, y)                                 # y sem efeitos fixos
  r2_parcial <- 1 - sum(e^2) / sum(yF^2)                   # completo × só efeitos fixos (0,2896)
  yw <- y - ave(y, a$ticker)                               # y centrado por empresa
  Xw <- sapply(variaveis, function(v) a[[v]] - ave(a[[v]], a$ticker))          # regressores centrados
  rw <- yw - Xw %*% b[pos]                                 # resíduo intra com os coeficientes de duas vias
  r2_intra <- 1 - sum(rw^2) / sum(yw^2)                    # convenção do PanelOLS (0,2130)

  modelo <- data.frame(modelo = nome, dependente = dependente, regressores = paste(variaveis, collapse = ";"),  # resumo: N/G/K e R² (Tabelas 7 e 8)
                       agrupamento = grupo, N = N, empresas = length(unique(a$ticker)), G = G, K = K,  # (continuação)
                       gl_residuo = N - K, anos = length(unique(a$ano)), primeiro = min(a$ano), ultimo = max(a$ano),  # (continuação)
                       R2_global = r2_global, R2_intra = r2_intra, R2_parcial = r2_parcial)   # resumo
  coefs <- data.frame(modelo = nome, variavel = variaveis, coef = b[pos], se_CR1 = se_cr1[pos], t_CR1 = t_cr1[pos],  # coeficiente e inferência CR1
                      p_CR1 = p_cr1[pos], IC_inf = b[pos] - crit * se_cr1[pos], IC_sup = b[pos] + crit * se_cr1[pos])  # IC de 95%
  if (wcr) {                                               # bootstrap por enumeração
    w <- t(sapply(pos, function(j) wild_cluster_restrito(X, y, P, g, G, j, fator_cr1, abs(t_cr1[j]))))  # contagens exatas do WCR
    coefs$p_WCR <- w[, 1] / w[, 2]; coefs$excedencias <- w[, 1]; coefs$combinacoes <- w[, 2]  # p WCR = excedências / combinações
  }
  if (dk) for (bw in DEFASAGENS_DK) {                      # Driscoll–Kraay
    s <- driscoll_kraay(X, e, F, a$ano, pos, bw)              # erros-padrão DK
    coefs[[paste0("se_DK", bw)]] <- s                         # guarda
    coefs[[paste0("p_DK", bw)]] <- 2 * pt(-abs(b[pos] / s), N - K)              # t(N−K)
  }
  list(modelo = modelo, coefs = coefs, X = X, y = y, e = e, P = P, F = F, pos = pos, dados = a)  # resumo, coeficientes e matrizes
}

wild_cluster_restrito <- function(X, y, P, g, G, j, fator_cr1, t_obs, bloco = BLOCO_WCR) {  # WCR por enumeração
  # 1) impõe β_j = 0; 2) y* = f0 + s_g·u para TODAS as 2^G combinações de sinais por grupo;
  # 3) reestima e calcula t* com CR1; 4) p = proporção de |t*| ≥ |t observado|.
  u <- qr.resid(qr(X[, -j, drop = FALSE]), y)              # resíduos restritos (modelo sem o fundamento j)
  f0 <- y - u                                              # ajustados sob H0
  total <- 2^G                                             # 16.384 com G = 14; 4.096 com G = 12
  exc <- 0                                                 # excedências
  for (inicio in seq(0, total - 1, by = bloco)) {          # blocos de combinações
    ids <- inicio:min(inicio + bloco - 1, total - 1)       # números das combinações
    sinais <- sapply(0:(G - 1), function(c) 2 * ((ids %/% 2^c) %% 2) - 1)       # bit c → sinal −1/+1 (comb × G)
    Y <- f0 + u * t(sinais[, g, drop = FALSE])             # N × combinações
    B <- P %*% Y                                           # coeficientes de todas as combinações
    E <- Y - X %*% B                                       # resíduos
    esc <- sapply(seq_len(G), function(c) colSums(P[j, g == c] * E[g == c, , drop = FALSE]))   # comb × G
    t_star <- B[j, ] / sqrt(fator_cr1 * rowSums(esc^2))    # t* com CR1
    exc <- exc + sum(abs(t_star) >= t_obs - TOL_EMPATE_WCR)   # conta |t*| ≥ |t observado|
  }
  c(exc, total)                                            # ex.: 42 de 16.384 (ROE)
}

driscoll_kraay <- function(X, e, F, anos, pos, bw) {       # erros-padrão DK dos fundamentos
  N <- nrow(X); K <- ncol(X)                               # tamanho e parâmetros
  Xt <- residualizar(F, X[, pos, drop = FALSE])            # fundamentos sem efeitos fixos
  h <- t(sapply(sort(unique(anos)), function(t) colSums(Xt[anos == t, , drop = FALSE] * e[anos == t])))   # T × k
  S <- crossprod(h); nT <- nrow(h)                         # variância no mesmo ano
  for (lag in seq_len(bw)) {                               # autocovariâncias até bw
    w <- 1 - lag / (bw + 1)                                # peso de Bartlett
    Gm <- t(h[(lag + 1):nT, , drop = FALSE]) %*% h[1:(nT - lag), , drop = FALSE]  # covariância entre anos a "lag" de distância
    S <- S + w * (Gm + t(Gm))                              # soma simétrica
  }
  A <- solve(crossprod(Xt))                                # "pão" do sanduíche
  sqrt(diag(A %*% S %*% A * N / (N - K)))                  # erros-padrão com N/(N−K)
}

holm <- function(p) {                                      # Holm (1979): 3p, 2p, 1p com monotonicidade
  o <- order(p)                                            # do menor para o maior
  aj <- pmin(cummax(p[o] * (length(p):1)), 1)              # multiplica e impõe ordem
  out <- numeric(length(p)); out[o] <- aj                  # volta à ordem original
  out                                                         # p ajustados
}

vif_intra <- function(F, Z) {                              # VIF após retirar os efeitos fixos
  co <- cor(residualizar(F, Z))                            # correlações intra
  list(vif = diag(solve(co)), corr = co)                   # VIF_j = [R⁻¹]_jj
}

fracao_fwl <- function(X, j) {                             # de onde vem a informação de β_j
  z <- residualizar(X[, -j, drop = FALSE], X[, j])         # x_j limpo das demais colunas
  z^2 / sum(z^2)                                           # soma 1 (CEB = 54,55% no ROE); não é causal
}
