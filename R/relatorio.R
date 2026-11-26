# =============================================================================
# relatorio.R — Relatório de reprodução em PDF
# =============================================================================
# Monta resultados/r/relatorio_reproducao.pdf (cerca de 27 páginas) a partir de
# relatorio/roteiro.txt (o mesmo arquivo da versão Python), dos resultados e dos
# valores publicados no TCC. Os números do texto são inseridos com
# {chave;decimais;tipo} pela mesma regra da conferência (valores.R).
# Diagramação: A4 em polegadas a partir do topo, mesma geometria da versão Python.
# Usa cairo_pdf (Unicode); sem cairo (ex.: macOS sem XQuartz), usa pdf() com WinAnsi.
# Equivale a python/tcc/relatorio.py.
# =============================================================================

LINGUAGEM <- "R"                                           # aparece na capa e no rodapé
.rel <- new.env()                                          # estado do relatório (tabelas e página)

br <- function(s) gsub("(\\d)\\.(\\d)", "\\1,\\2",         # ponto decimal → vírgula
                       gsub("(?<![\\w/.])-(?=\\d)", "−", s, perl = TRUE), perl = TRUE)   # hífen → sinal de menos

carregar_relatorio <- function() {                         # resultados e conferência com o TCC
  s <- RESULTADOS                                             # pasta resultados/
  .rel$cap <- ler(file.path(s, "capitalizacao.csv"))       # decisões de capitalização
  .rel$dec <- ler(file.path(s, "decisoes_amostra.csv"))    # inclusão de cada empresa-ano
  .rel$fin <- ler(file.path(s, "financeiro.csv"))          # fundamentos por exercício
  .rel$cor <- ler(file.path(s, "correcoes_lucro.csv"))     # conciliação do lucro
  carregar_resultados(s)                                   # tabelas usadas pelas chaves
  pub <- read.csv(file.path(DADOS, "documentos", "valores_publicados_tcc.csv"), colClasses = "character",  # 465 valores publicados, como texto
                  encoding = "UTF-8", check.names = FALSE)    # (continuação)
  pub$calculado <- mapply(function(c, dc, t) formatar(valor(c), dc, t), pub$chave, pub$decimais, pub$tipo)  # recalcula e formata
  pub$confere <- pub$calculado == pub$publicado            # mesma comparação de conferencia.R
  .rel$pub <- pub; .rel$n_ok <- sum(pub$confere); .rel$n_tot <- nrow(pub)   # 465 de 465
}

# =============================================================================
# Tabelas montadas na hora: list(titulo, cab, linhas, nota)
# =============================================================================
tb <- function(titulo, cab, linhas, nota) list(titulo = titulo, cab = cab, linhas = linhas, nota = nota)  # construtor de tabela: título, cabeçalho, linhas e nota
MOTIVO <- c(excluir_capital_ambiguo_ou_ausente = "capital ausente ou ambíguo no FRE",            # status → texto
            excluir_preco_classe_ausente = "sem cotação de dezembro de alguma classe",  # (continuação)
            excluir_subclasses_ou_tesouraria = "subclasses PNA/PNB sem repartição única documentada",  # (continuação)
            excluir_divergencia_tesouraria_DFP_FRE = "tesouraria do FRE diverge da DFP",  # (continuação)
            excluir_divergencia_tesouraria_FRE = "tesouraria do FRE ambígua",  # (continuação)
            excluir_tesouraria_nao_documentada = "tesouraria não documentada",  # (continuação)
            excluir_tesouraria_evento_posterior = "evento societário posterior com tesouraria",  # (continuação)
            excluir_quantidade_invalida = "quantidade de ações inválida")  # (fim)

nota_capital <- function(n) {                              # coluna `nota` → texto legível
  if (startsWith(n, "http")) return("quantidade transcrita da DF original (6-K na SEC)")   # CPFL
  trad <- c(nota26_2020 = "quantidades da nota 26 das DFs (6-K na SEC)",                    # Cemig 2020
            DFP_liquido_reconciliado_FRE = "DFP já sem tesouraria: emitidas recuperadas no FRE",   # Neoenergia
            DF2011_nota26_p26 = "DF de 2011, nota 26, p. 26")                                 # EDP
  partes <- sapply(strsplit(n, ";")[[1]], function(x)      # cada decisão registrada
    if (startsWith(x, "desfeito_evento_")) paste0("evento aprovado em ", substring(x, 17), " desfeito")   # Copel 2020
    else if (x %in% names(trad)) trad[[x]] else x)            # demais decisões
  paste(partes, collapse = "; ")                              # texto final
}

t_decisoes <- function() {                                 # decisões na quantidade de ações e escalas em milhares
  cap <- .rel$cap; dec <- .rel$dec; d <- .res$d               # tabelas usadas
  c <- cap[!is.na(cap$nota) & cap$nota != "", ]            # empresas-ano com decisão registrada
  k <- match(paste(c$ticker, c$ano), paste(dec$ticker, dec$ano))            # inclusão nos painéis
  linhas <- lapply(seq_len(nrow(c)), function(i) c(c$ticker[i], as.character(c$ano[i]),  # empresa, ano e painel
    if (dec$incluido_principal[k[i]]) "sim" else if (dec$incluido_historico[k[i]]) "histórico" else "não", nota_capital(c$nota[i])))  # (continuação)
  e <- cap[!is.na(cap$escala) & cap$escala == 1000 & cap$ano >= 2020 & cap$ano <= 2025 & cap$ticker %in% d$ticker, ]   # milhares
  tk <- sort(unique(e$ticker), method = "radix")              # empresas com escala em milhares
  list(tb("Decisões documentadas na quantidade de ações", c("Empresa", "Ano", "No painel", "Decisão"), linhas,  # tabela de decisões
          "Fonte: capitalizacao.csv (coluna nota). 'Histórico': só na extensão 2012–2025."),  # nota
       tb("Empresas do painel com quantidades informadas em milhares (2020–2025)", c("Empresa", "Anos multiplicados por mil"),  # tabela de escalas
          lapply(tk, function(t) c(t, paste(sort(e$ano[e$ticker == t]), collapse = ", "))),  # anos por empresa
          "A escala é a que faz a quantidade da DFP coincidir com o capital do FRE."))  # nota
}

t_correcoes <- function() {                                # conciliação do lucro (Light e Serena)
  sit <- c(confirmado_DRE_individual_igual_consolidado = "DRE individual confirmou o total consolidado",  # status → situação
           excluido_lucro_inconsistente = "não conciliado: lucro fica ausente")  # (continuação)
  f <- function(x) if (is.na(x)) "—" else formatar(x / 1e9, 2, "num")       # R$ bilhões
  co <- .rel$cor                                              # registro das correções
  list(tb("Conciliação do lucro da controladora (R$ bilhões)", c("Empresa", "Exercício", "Antes", "Usado", "Situação"),  # tabela de correções
          lapply(seq_len(nrow(co)), function(i) c(co$ticker[i], as.character(co$ano[i]), f(co$anterior[i]), f(co$corrigido[i]),  # empresa, exercício, antes e depois
                                                  sit[[co$status[i]]])),  # situação
          "Light 2025 afetaria só o mercado de 2026, fora do painel. A Serena ficou fora do painel por outros motivos."))  # nota
}

t_funil <- function() {                                    # 138 → 90 → 84 → 76
  nm <- c(combinacoes = "Combinações possíveis (23 emissoras × 6 anos)", capitalizacao_conciliada = "Com capitalização conciliada",  # etapas do funil
          tres_fundamentos_validos = "Com os três fundamentos do ano anterior",  # (continuação)
          minimo_quatro_anos = "Com mínimo de quatro exercícios por empresa (painel principal)")  # (fim)
  list(tb("Funil da amostra principal (2020–2025)", c("Etapa", "Empresas-ano"),  # tabela do funil
          lapply(names(nm), function(k) c(nm[[k]], as.character(.res$fun[[k]]))), "Resultado: 76 observações de 14 empresas."))  # contagens
}

t_lacunas <- function() {                                  # motivo de cada ano ausente (8 lacunas)
  dec <- .rel$dec; fin <- .rel$fin; linhas <- list()          # decisões, fundamentos e saída
  for (e in sort(unique(.res$d$ticker), method = "radix")) for (a in 2020:2025) {   # empresas × anos
    r <- dec[dec$ticker == e & dec$ano == a, ][1, ]        # decisão da empresa-ano
    if (isTRUE(r$incluido_principal)) next                 # presente: não é lacuna
    if (r$status != "ok") {                                # falhou na capitalização
      mot <- if (r$status %in% names(MOTIVO)) MOTIVO[[r$status]] else r$status  # motivo da capitalização
    } else {                                               # falhou nos fundamentos de t−1
      f <- fin[fin$ticker == e & fin$ano == a - 1, ]          # exercício t−1
      if (nrow(f) == 0) mot <- "sem demonstração do ano anterior" else {  # sem DFP do ano anterior
        m <- c()                                           # motivos
        if (is.na(f$roe[1])) m <- c(m, if (is.na(f$lucro_controladora[1])) "lucro da controladora não conciliado"  # ROE ausente: lucro não conciliado ou PL ≤ 0
                                        else sprintf("PL de %d não positivo: ROE não calculável", a - 1))  # (continuação)
        if (is.na(f$dl[1])) m <- c(m, sprintf("EBITDA de %d não positivo: alavancagem não calculável", a - 1))  # AL ausente: EBITDA ≤ 0
        mot <- paste(m, collapse = "; ")                      # junta os motivos
      }
    }
    linhas[[length(linhas) + 1]] <- c(e, as.character(a), mot)  # registra a lacuna
  }
  list(tb("Anos ausentes das empresas do painel principal", c("Empresa", "Ano de mercado", "Motivo"), linhas,  # tabela de lacunas
          "Fundamentos do ano anterior ao de mercado. Nenhum valor ausente foi preenchido."))  # nota
}

t_conf_resumo <- function() {                              # conferência com o TCC, por tabela
  pub <- .rel$pub; tabs <- unique(pub$tabela)                 # valores e origens
  linhas <- lapply(tabs, function(t) c(t, as.character(sum(pub$tabela == t)), as.character(sum(pub$confere[pub$tabela == t]))))  # valores e acertos por origem
  linhas[[length(linhas) + 1]] <- c("Total", as.character(.rel$n_tot), as.character(.rel$n_ok))  # linha de total
  list(tb("Valores do TCC recalculados", c("Origem no TCC", "Valores", "Coincidem"), linhas,  # tabela-resumo
          "Comparação do texto formatado: mesmas casas decimais, vírgula e '< 0,0001'."))  # nota
}

t_conf_detalhe <- function() {                             # anexo: os 465 valores
  pub <- .rel$pub                                             # valores
  list(tb("", c("Origem", "Linha", "Item", "Publicado", "Calculado", "Confere"),  # anexo
          lapply(seq_len(nrow(pub)), function(i) c(pub$tabela[i], pub$linha[i], pub$item[i], pub$publicado[i], pub$calculado[i],  # uma linha por valor
                                                   if (pub$confere[i]) "sim" else "NÃO")), ""))  # sim/NÃO
}
DINAMICAS <- list(decisoes_capital = t_decisoes, correcoes_lucro = t_correcoes, funil = t_funil, lacunas = t_lacunas,  # diretiva @nome → função
                  conferencia_resumo = t_conf_resumo, conferencia_detalhe = t_conf_detalhe)   # diretiva → função

# =============================================================================
# Leitura do roteiro
# =============================================================================
substituir <- function(s) {                                # {chave;decimais;tipo} → número formatado
  m <- gregexpr("\\{([^{};]+);(\\d+);(\\w+)\\}", s, perl = TRUE)  # posições dos marcadores
  regmatches(s, m) <- list(vapply(regmatches(s, m)[[1]], function(x) {  # substitui cada marcador
    p <- strsplit(substr(x, 2, nchar(x) - 1), ";", fixed = TRUE)[[1]]; formatar(valor(p[1]), p[2], p[3]) }, ""))  # chave, decimais e tipo → texto
  s                                                           # linha pronta
}

ler_roteiro <- function() {                                # roteiro → lista de blocos
  blocos <- list(); par_ <- c(); lista <- c(); tab <- c(); nomes <- c()     # saída e acumuladores
  add <- function(b) blocos[[length(blocos) + 1]] <<- b    # acrescenta um bloco
  fecha <- function() {                                    # encerra parágrafo, lista ou tabela em construção
    if (length(par_)) { txt <- paste(par_, collapse = " ")    # parágrafo
      if (startsWith(txt, "> ")) add(list("box", substring(txt, 3))) else add(list("p", txt)) }  # quadro ("> ") ou parágrafo
    if (length(lista)) add(list("ul", lista))                 # lista
    if (length(tab)) {                                     # tabela fixa em markdown
      tab <- tab[!grepl("^\\|\\s*-", tab)]                 # ignora a linha | --- |
      ls <- lapply(tab, function(l) trimws(strsplit(gsub("^\\s*\\||\\|\\s*$", "", l), "|", fixed = TRUE)[[1]]))  # células da tabela fixa
      add(list("tabela", tb("", ls[[1]], ls[-1], "")))        # tabela
    }
    par_ <<- c(); lista <<- c(); tab <<- c()                  # zera os acumuladores
  }
  for (linha in readLines(ROTEIRO, encoding = "UTF-8")) {  # cada linha do roteiro
    if (startsWith(linha, "%")) next                       # comentário
    linha <- substituir(sub("\\s+$", "", linha))           # insere os números calculados
    if (!nzchar(trimws(linha))) fecha()                    # linha em branco separa blocos
    else if (startsWith(linha, "@nomes ")) {               # rótulos das variáveis
      for (x in strsplit(substring(linha, 8), ";", fixed = TRUE)[[1]]) {  # cada par chave=rótulo
        kv <- regmatches(x, regexpr("=", x), invert = TRUE)[[1]]; nomes[kv[1]] <- kv[2] }  # guarda o rótulo
    } else if (startsWith(linha, "## ")) { fecha(); add(list("h2", substring(linha, 4))) }      # seção
    else if (startsWith(linha, "### ")) { fecha(); add(list("h3", substring(linha, 5))) }       # subseção
    else if (startsWith(linha, "- ")) { if (length(par_)) fecha(); lista <- c(lista, substring(linha, 3)) }   # item
    else if (startsWith(linha, "|")) tab <- c(tab, linha)  # linha de tabela fixa
    else if (startsWith(linha, "@formula ")) { fecha(); add(list("formula", substring(linha, 10))) }   # fórmula
    else if (startsWith(linha, "@tabela ")) {              # tabela de resultados/tabelas_tcc
      fecha()                                                 # fecha o bloco anterior
      p <- trimws(strsplit(substring(linha, 9), "|", fixed = TRUE)[[1]])    # arquivo | título | nota | cabeçalhos
      df <- read.csv(file.path(TABELAS, p[1]), colClasses = "character", encoding = "UTF-8", check.names = FALSE)  # lê a tabela como texto
      ls <- lapply(seq_len(nrow(df)), function(i) br(vapply(unlist(df[i, ]), function(v) if (v %in% names(nomes)) nomes[[v]] else v, "")))  # rótulos e vírgula decimal
      add(list("tabela", tb(p[2], strsplit(p[4], ";", fixed = TRUE)[[1]], ls, p[3])))  # tabela com título, cabeçalho e nota
    } else if (startsWith(linha, "@")) {                   # demais diretivas
      fecha(); nome <- trimws(substring(linha, 2))            # nome da diretiva
      if (nome %in% names(DINAMICAS)) for (t in DINAMICAS[[nome]]()) add(list("tabela", t)) else add(list(nome))  # tabela dinâmica ou diretiva simples
    } else { if (length(lista)) fecha(); par_ <- c(par_, trimws(linha)) }  # texto corrido
  }
  fecha()                                                     # fecha o último bloco
  blocos                                                      # lista de blocos
}

# =============================================================================
# Diagramação (A4, polegadas a partir do topo)
# =============================================================================
PW <- 8.27; PH <- 11.69; ML <- 0.85; MR <- 0.85; MT <- 0.85; MB <- 0.95   # página e margens
W <- PW - ML - MR; CW <- 0.55; CWT <- 0.62                 # largura útil e largura média de caractere
AZUL <- "#1F3A5F"; AZUL_CLARO <- "#EAF2F8"; CINZA <- "#F2F4F7"            # cores

quebrar <- function(txt, n) {                              # quebra gulosa por palavras (igual à do Python)
  pal <- strsplit(trimws(txt), "\\s+")[[1]]; linhas <- c(); atual <- ""  # palavras e acumuladores
  for (p in pal) {                                            # cada palavra
    if (!nzchar(atual)) atual <- p                         # primeira palavra
    else if (nchar(atual) + 1 + nchar(p) <= n) atual <- paste(atual, p)      # cabe
    else { linhas <- c(linhas, atual); atual <- p }        # não cabe: nova linha
  }
  if (nzchar(atual)) linhas <- c(linhas, atual)               # última linha
  if (length(linhas)) linhas else ""                          # nunca vazio
}
nchar_l <- function(largura, tam) max(1, floor(largura * 72 / (tam * CW)))  # caracteres que cabem na largura

limpa <- function(s) {                                     # sem cairo: troca símbolos fora do CP1252
  if (.rel$cairo) return(s)                                   # com cairo, nada a trocar
  for (p in list(c("−", "-"), c("→", "->"), c("Σ", "soma"), c("≥", ">="), c("≤", "<="))) s <- gsub(p[1], p[2], s, fixed = TRUE)  # troca símbolo a símbolo
  s                                                           # texto limpo
}
inicia_pagina <- function() {                              # coordenadas em polegadas, y para baixo
  par(mar = c(0, 0, 0, 0), xaxs = "i", yaxs = "i", fig = c(0, 1, 0, 1))  # sem margens, página inteira
  plot.new(); plot.window(c(0, PW), c(PH, 0))                 # y cresce para baixo
}
volta_pagina <- function() {                               # depois de um gráfico, volta às coordenadas da página
  par(fig = c(0, 1, 0, 1), mar = c(0, 0, 0, 0), new = TRUE, xaxs = "i", yaxs = "i")  # volta à página inteira
  plot.new(); plot.window(c(0, PW), c(PH, 0))                 # mesmas coordenadas
}
texto <- function(x, y, s, tam, peso = 1, cor = "black", ha = 0)           # texto com o topo em (x, y)
  text(x, y, limpa(s), adj = c(ha, 1), cex = tam / 12, font = peso, col = cor, xpd = NA)  # adj = topo à esquerda
ret <- function(x, y, w, h, cor) rect(x, y, x + w, y + h, col = cor, border = NA, xpd = NA)      # retângulo
linha_h <- function(x0, x1, y, cor, esp = 0.8) segments(x0, y, x1, y, col = cor, lwd = esp * 1.3, xpd = NA)   # fio
rodape <- function() if (.rel$n > 1) {                     # rodapé (exceto na capa)
  texto(ML, PH - 0.55, paste("Relatório de reprodução do TCC — versão", LINGUAGEM), 7.5, cor = "#777777")
  texto(PW - MR, PH - 0.55, paste("página", .rel$n), 7.5, cor = "#777777", ha = 1)
}
nova <- function() { if (.rel$n > 0) rodape(); inicia_pagina(); .rel$n <- .rel$n + 1; .rel$y <- MT }   # página nova
cabe <- function(alt) if (.rel$y + alt > PH - MB) nova()   # quebra de página se o bloco não couber

paragrafo <- function(txt, tam = 9.5, recuo = 0, marcador = NULL, depois = 0.09) {   # parágrafo
  lh <- tam * 1.42 / 72; ls <- quebrar(txt, nchar_l(W - recuo, tam))       # entrelinha e linhas
  for (i in seq_along(ls)) {                                  # cada linha
    cabe(lh)                                                  # quebra de página se preciso
    if (i == 1 && !is.null(marcador)) texto(ML + recuo - 0.15, .rel$y, marcador, tam)   # marcador de lista
    texto(ML + recuo, .rel$y, ls[i], tam); .rel$y <- .rel$y + lh  # escreve e desce
  }
  .rel$y <- .rel$y + depois                                   # espaço após o parágrafo
}
h2 <- function(txt) { nova(); texto(ML, .rel$y, txt, 15, 2, AZUL); .rel$y <- .rel$y + 0.32      # seção em página nova
  linha_h(ML, PW - MR, .rel$y, AZUL, 1.2); .rel$y <- .rel$y + 0.18 }  # fio azul
h3 <- function(txt) { cabe(0.6); .rel$y <- .rel$y + 0.1; texto(ML, .rel$y, txt, 11.5, 2, AZUL); .rel$y <- .rel$y + 0.27 }  # subseção
caixa <- function(txt) {                                   # quadro de destaque
  tam <- 9.5; lh <- tam * 1.42 / 72; ls <- quebrar(txt, nchar_l(W - 0.35, tam)); alt <- length(ls) * lh + 0.2  # fonte, entrelinha, linhas e altura
  cabe(alt); ret(ML, .rel$y, W, alt, AZUL_CLARO); ret(ML, .rel$y, 0.05, alt, "#1F6FB2")    # fundo e barra
  y <- .rel$y + 0.1; for (l in ls) { texto(ML + 0.2, y, l, tam); y <- y + lh }  # linhas do quadro
  .rel$y <- .rel$y + alt + 0.12                               # espaço após
}
formula_ <- function(txt) { cabe(0.4); .rel$y <- .rel$y + 0.06; texto(PW / 2, .rel$y, txt, 10.5, 3, ha = 0.5); .rel$y <- .rel$y + 0.34 }  # fórmula centralizada em itálico

tabela <- function(t, tam = 8) {                           # tabela zebrada com cabeçalho repetido
  linhas <- t$linhas; cab <- t$cab; ncol <- length(cab)       # linhas, cabeçalho e número de colunas
  if (length(linhas) > 60) tam <- 7                        # anexo em fonte menor
  pad <- 0.05; lh <- tam * 1.3 / 72                        # margem interna e altura de linha
  comp <- sapply(seq_len(ncol), function(j) min(max(c(nchar(cab[j]), vapply(linhas, function(r) nchar(r[j]), 0))), 60))   # caracteres por coluna
  total <- max(1, floor(W * 72 / (tam * CWT))) - 2 * ncol  # caracteres que cabem
  if (sum(comp) > total) { lim <- max(comp); while (sum(pmin(comp, lim)) > total) lim <- lim - 1; comp <- pmin(comp, lim) }   # reduz as largas
  larg <- (comp + 2) * tam * CWT / 72; larg <- larg * W / sum(larg)          # largura de cada coluna, esticada
  xs <- c(ML, ML + cumsum(larg))                           # posição das colunas
  cel <- function(r) lapply(seq_len(ncol), function(j) if (nchar(r[j]) > comp[j]) quebrar(r[j], comp[j]) else r[j])   # quebra nas células
  cab_q <- cel(cab); alt_cab <- max(lengths(cab_q)) * lh + 2 * pad  # cabeçalho quebrado e sua altura
  desenha_cab <- function() {                              # faixa azul com os nomes das colunas
    ret(ML, .rel$y, sum(larg), alt_cab, AZUL)                 # faixa azul
    for (j in seq_along(cab_q)) for (k in seq_along(cab_q[[j]])) texto(xs[j] + pad, .rel$y + pad + (k - 1) * lh, cab_q[[j]][k], tam, 2, "white")  # nomes das colunas em branco
    .rel$y <- .rel$y + alt_cab                                # desce
  }
  if (nzchar(t$titulo)) { cabe(0.3 + alt_cab + 2 * lh); .rel$y <- .rel$y + 0.06; texto(ML, .rel$y, t$titulo, 9.5, 2); .rel$y <- .rel$y + 0.24 }  # título acima da tabela
  else cabe(alt_cab + 2 * lh)                                 # sem título
  desenha_cab()                                               # cabeçalho
  for (i in seq_along(linhas)) {                           # cada linha
    r <- linhas[[i]]; q <- cel(r); alt <- max(lengths(q)) * lh + 2 * pad  # linha, células quebradas e altura
    if (.rel$y + alt > PH - MB) { nova(); desenha_cab() }  # página nova com cabeçalho repetido
    if (i %% 2 == 0) ret(ML, .rel$y, sum(larg), alt, CINZA)                 # zebrado
    for (j in seq_along(q)) for (k in seq_along(q[[j]]))      # cada célula
      texto(xs[j] + pad, .rel$y + pad + (k - 1) * lh, q[[j]][k], tam, if (r[j] == "NÃO") 2 else 1, if (r[j] == "NÃO") "#B00020" else "black")
    .rel$y <- .rel$y + alt                                    # desce
  }
  linha_h(ML, ML + sum(larg), .rel$y, AZUL, 0.8); .rel$y <- .rel$y + 0.05  # fio de fechamento
  if (nzchar(t$nota)) paragrafo(paste("Nota:", t$nota), tam = 7.6, depois = 0.05)  # nota da tabela
  .rel$y <- .rel$y + 0.1                                      # espaço após
}

figura1 <- function() {                                    # Figura 1 do TCC na página
  alt <- 4.4; cabe(alt + 0.6); .rel$y <- .rel$y + 0.06        # altura reservada
  texto(ML, .rel$y, "Figura 1. Coeficientes após a retirada de cada empresa", 9.5, 2); .rel$y <- .rel$y + 0.25  # título da figura
  esq <- ML + 1.25; lp <- (W - 1.25 - 0.3) / 3; sep <- 0.15                # três painéis lado a lado
  for (k in 1:3) {                                            # três painéis
    x0 <- esq + (k - 1) * (lp + sep)                          # posição horizontal do painel
    par(fig = c(x0 / PW, (x0 + lp - sep) / PW, 1 - (.rel$y + alt - 0.45) / PH, 1 - .rel$y / PH), new = TRUE, xaxs = "r", yaxs = "r")  # região do painel na página
    desenhar_painel_figura1(.res$coef, .res$d, k)          # mesmo desenho do PNG (tabelas.R)
  }
  volta_pagina()                                              # volta às coordenadas da página
  .rel$y <- .rel$y + alt                                      # desce
  paragrafo(paste("Nota: pontos = coeficiente estimado sem a empresa indicada; barras = intervalo CR1 de 95%;",  # nota da figura
                  "linha tracejada = modelo principal; losango = retirada da CEB."), tam = 7.6)  # (continuação)
  .rel$y <- .rel$y + 0.08                                     # espaço após
}

capa <- function() {                                       # capa com resumo da conferência
  nova(); ret(0, 0, PW, 3.6, AZUL)                         # faixa azul no topo
  texto(ML, 1.3, "Relatório de reprodução", 26, 2, "white")   # título
  texto(ML, 1.95, "Fundamentos contábeis e capitalização de mercado", 14, cor = "white")  # subtítulo
  texto(ML, 2.25, "de empresas elétricas brasileiras", 14, cor = "white")  # (continuação)
  texto(ML, 2.8, "Rodrigo Pereira Fontes · Orientador: Prof. Marco Antonio Alves de Souza Junior", 10, cor = "#D6E4F0")   # autoria
  texto(ML, 3.05, "MBA em Finanças e Controladoria · USP/Esalq · 2026", 10, cor = "#D6E4F0")        # curso
  .rel$y <- 4.3                                               # abaixo da faixa
  caixa(paste0("Gerado em ", format(Sys.Date(), "%d/%m/%Y"), " pela versão em ", LINGUAGEM,  # data, linguagem e origem dos dados
               " do pacote de reprodução, a partir dos extratos preservados da CVM e da B3, sem acesso à internet."))  # (continuação)
  sit <- if (.rel$n_ok == .rel$n_tot) "todos coincidem" else paste(.rel$n_tot - .rel$n_ok, "divergem")  # situação da conferência
  paragrafo(sprintf("Conferência com o texto do TCC: %d de %d valores coincidem (%s).", .rel$n_ok, .rel$n_tot, sit), 11, depois = 0.12)  # 465 de 465
  paragrafo(sprintf("Painel principal: %d observações de %d empresas, 2020–2025. Painel histórico: %d observações de %d empresas, 2012–2025.",  # tamanho dos painéis
                    as.integer(.res$fun[["minimo_quatro_anos"]]), length(unique(.res$d$ticker)), nrow(.res$h), length(unique(.res$h$ticker))),  # (continuação)
            11, depois = 0.12)                                # (fim)
  r <- function(v, c) formatar(valor(paste0(c, "|principal|", v)), 4, if (startsWith(c, "p")) "p" else "num")  # atalho: valor formatado
  paragrafo(paste0("Modelo principal (coeficiente; p WCR): ROE ", r("roe_lag", "coef"), "; ", r("roe_lag", "p_WCR"),  # resultado principal
                   " · Alavancagem ", r("dl_lag", "coef"), "; ", r("dl_lag", "p_WCR"),  # (continuação)
                   " · Porte ", r("size_lag", "coef"), "; ", r("size_lag", "p_WCR")), 11)  # (fim)
}

gerar_relatorio <- function() {                            # monta e grava o PDF
  carregar_relatorio()                                     # resultados e conferência
  blocos <- ler_roteiro()                                  # blocos na ordem do roteiro
  destino <- file.path(RESULTADOS, "relatorio_reproducao.pdf")  # arquivo de saída
  .rel$cairo <- isTRUE(capabilities("cairo"))              # cairo disponível?
  if (.rel$cairo) cairo_pdf(destino, width = PW, height = PH, family = "sans", onefile = TRUE) else   # Unicode
    pdf(destino, width = PW, height = PH, family = "Helvetica", encoding = "WinAnsi.enc", onefile = TRUE)   # alternativa
  .rel$n <- 0; .rel$y <- MT                                # contador de páginas e cursor
  for (b in blocos) switch(b[[1]],                         # cada bloco vira texto, tabela ou figura
    capa = capa(), h2 = h2(b[[2]]), h3 = h3(b[[2]]), p = paragrafo(b[[2]]), box = caixa(b[[2]]),  # blocos simples
    ul = { for (it in b[[2]]) paragrafo(it, recuo = 0.2, marcador = "•", depois = 0.04); .rel$y <- .rel$y + 0.06 },  # lista: um parágrafo por item
    formula = formula_(b[[2]]), tabela = tabela(b[[2]]), figura1 = figura1(), pagina = NULL,  # fórmula, tabela, figura
    stop("diretiva desconhecida: ", b[[1]]))                  # diretiva desconhecida = erro
  rodape(); invisible(dev.off())                           # fecha o PDF
  cat(sprintf("  relatorio_reproducao.pdf: %d páginas; conferência com o TCC: %d de %d valores coincidem\n",  # resumo no console
              .rel$n, .rel$n_ok, .rel$n_tot))                 # (continuação)
  invisible(destino)                                          # caminho do PDF
}
