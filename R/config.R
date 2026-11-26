# =============================================================================
# config.R — Parâmetros e caminhos do estudo
# =============================================================================
# Todas as escolhas metodológicas usadas em mais de um módulo ficam aqui, com a
# justificativa e a seção do TCC de onde vêm. Equivale a python/tcc/config.py.
#
# Referências: Collins, Maydew e Weiss (1997); Barth, Beaver e Landsman (2001)
# (relevância informacional); Cameron e Miller (2015); MacKinnon, Nielsen e
# Webb (2023) (inferência com poucos grupos).
# =============================================================================

# Textos em UTF-8 (nomes como "Ordinária"); no Windows, o R >= 4.2 já usa UTF-8
if (!l10n_info()$`UTF-8`) invisible(suppressWarnings(Sys.setlocale("LC_CTYPE", "C.UTF-8")))  # garante UTF-8
options(stringsAsFactors = FALSE)                          # textos nunca viram fatores

# -----------------------------------------------------------------------------
# Caminhos (RAIZ, a raiz do repositório, é definido por R/executar.R)
# -----------------------------------------------------------------------------
DADOS      <- file.path(RAIZ, "dados")                     # extratos congelados da coleta (entrada)
REFERENCIA <- file.path(RAIZ, "referencia")                # saídas do pacote original (só para conferência)
ROTEIRO    <- file.path(RAIZ, "relatorio", "roteiro.txt")  # texto do relatório (o mesmo da versão Python)
RESULTADOS <- file.path(RAIZ, "resultados", "r")           # saídas da versão R (a Python grava em resultados/python)
TABELAS    <- file.path(RESULTADOS, "tabelas_tcc")         # tabelas no formato do TCC

# -----------------------------------------------------------------------------
# Amostra (TCC, "Seleção da amostra" e "Painel")
# -----------------------------------------------------------------------------
ANOS_COLETA          <- 2010:2025                          # anos de mercado com cotação de dezembro
ANO_INICIO_PRINCIPAL <- 2020                               # painel principal: 2020–2025
ANO_FIM              <- 2025                               # último ano de mercado
ANO_INICIO_HISTORICO <- 2010                               # extensão histórica (2010–2011 caem: só uma empresa)
MIN_EXERCICIOS       <- 4                                  # mínimo de anos por empresa (efeito fixo usa a variação interna)
MIN_EMPRESAS_ANO     <- 2                                  # ano com uma só empresa não tem comparação transversal
PERCENTIS_WINSOR     <- c(0.01, 0.99)                      # winsorização de ROE e alavancagem (Tabela 3, nota)

# -----------------------------------------------------------------------------
# Variáveis do modelo (eq. 7 do TCC)
# -----------------------------------------------------------------------------
FUNDAMENTOS <- c("roe_lag", "dl_lag", "size_lag")          # ROE (eq. 3), AL (eq. 5) e PORTE (eq. 6), em t−1
DEPENDENTE  <- "ln_mcap"                                   # y = ln(VM), eq. (2): capitalização de dezembro de t

# -----------------------------------------------------------------------------
# Conciliação contábil e acionária (TCC, "Conciliação dos dados contábeis e acionários")
# -----------------------------------------------------------------------------
TOLERANCIA_LUCRO <- 1000                                   # R$ 1 mil entre lucro total e controladora + não controladores
ESCALAS          <- c(1, 1000)                             # quantidades de ações em unidades ou em milhares
JANELA_EVENTO    <- "06-30"                                # eventos até 30/06 do ano seguinte, já na DFP, são desfeitos
RAIZ_ANTIGA      <- list(EGIE = list("TBLE", 2015),        # Engie Brasil = Tractebel Energia até 2015
                         ENEV = list("MPXE", 2012))        # Eneva = MPX Energia até 2012
CEMIG_2020       <- list(on = 507670289, pn = 1011082312,  # Cemig (2021): DFs de 2020, nota 26 (6-K na SEC)
                         ton = 71, tpn = 583709)           # tesouraria: 71 ON e 583.709 PN
EDP_2010_2011    <- list(on = 158805204, pn = 0,           # EDP (2012): DF de 2011, nota 26, p. 26
                         ton = 280225, tpn = 0)            # tesouraria: 280.225 ON

# -----------------------------------------------------------------------------
# Sensibilidades (TCC, "Inferência e verificações de sensibilidade"; Apêndice C)
# -----------------------------------------------------------------------------
TRANSICOES <- list(CEBR3 = c(2021, 2022),                  # CEB: venda da CEB-D (CEB, 2022)
                   AURE3 = 2022:2025,                      # Auren: CESP e AES Brasil (Auren Energia, 2025)
                   LIGT3 = c(2023, 2024))                  # Light: recuperação judicial (Light, 2023)
GRUPOS_SOCIETARIOS <- c(EKTR3 = "NEOE3", TAEE3 = "CMIG3")  # Elektro–Neoenergia; Taesa–Cemig (cocontrole com a ISA)
DIA_MINIMO_COTACAO <- 20                                   # filtro de liquidez: último negócio a partir de 20/dez

# -----------------------------------------------------------------------------
# Inferência (TCC, Apêndice B)
# -----------------------------------------------------------------------------
NIVEL          <- 0.05                                     # referência de significância
BLOCO_WCR      <- 4096                                     # combinações de sinais processadas por vez
TOL_EMPATE_WCR <- 1e-10                                    # tolerância numérica para |t*| >= |t observado|
DEFASAGENS_DK  <- 1:2                                      # Driscoll–Kraay: Bartlett com 1 e 2 defasagens

NOMES_EMPRESAS <- c(AURE3 = "Auren", CEBR3 = "CEB", CLSC3 = "Celesc", CMIG3 = "Cemig",   # rótulos das 14 empresas
                    CPFE3 = "CPFL", EGIE3 = "Engie", EKTR3 = "Elektro", ENEV3 = "Eneva",  # (continuação)
                    EQTL3 = "Equatorial", GEPA3 = "Rio Paranapanema", LIGT3 = "Light",  # (continuação)
                    NEOE3 = "Neoenergia", REDE3 = "Rede", TAEE3 = "Taesa")  # (fim)

# -----------------------------------------------------------------------------
# Utilitários de leitura e escrita (usados por todos os módulos)
# -----------------------------------------------------------------------------
ler <- function(arq, ...) read.csv(arq, check.names = FALSE, stringsAsFactors = FALSE,   # nomes como "2.03" preservados
                                   encoding = "UTF-8", ...)                               # acentos corretos
gravar <- function(df, arq) write.csv(df, arq, row.names = FALSE, na = "", fileEncoding = "UTF-8")   # ausente = vazio
verdade <- function(x) !is.na(x) & x                       # NA conta como FALSO (mesmo comportamento do pandas)

para_json <- function(x, nivel = 0) {                      # JSON simples, sem dependências
  ind <- strrep("  ", nivel + 1); fim <- strrep("  ", nivel)                             # recuos
  if (is.list(x) || (!is.null(names(x)) && length(x) > 1)) {                             # objeto
    x <- as.list(x)                                           # vetor nomeado → lista
    itens <- vapply(names(x), function(n) paste0(ind, '"', n, '": ', para_json(x[[n]], nivel + 1)), "")  # "chave": valor
    return(paste0("{\n", paste(itens, collapse = ",\n"), "\n", fim, "}"))  # objeto JSON
  }
  if (is.matrix(x)) return(paste0("[", paste(apply(x, 1, function(r)                     # matriz → lista de listas
    paste0("[", paste(format(r, digits = 17), collapse = ", "), "]")), collapse = ", "), "]"))  # linha da matriz
  if (is.character(x)) return(paste0('"', x, '"'))                                       # texto
  format(x, digits = 17)                                                                 # número com precisão total
}
json_num <- function(arq, chave) {                         # lê um número de um JSON simples
  l <- grep(paste0('"', chave, '"'), readLines(arq, encoding = "UTF-8"), value = TRUE)[1]   # linha da chave
  as.numeric(sub(".*:\\s*\"?([-0-9.eE]+)\"?,?\\s*$", "\\1", l))                           # valor após os dois-pontos
}
