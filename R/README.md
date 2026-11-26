# Versão R — módulos em R base

Implementação em R do pacote de reprodução, só com R base (≥ 4.2). A estatística é escrita com álgebra de matrizes (`qr`, `backsolve`, `crossprod`). O pacote fixest, se instalado, entra apenas na conferência B, como verificação independente.

## Execução

```r
# Terminal, na raiz do repositório:
#   Rscript R/executar.R
# RStudio: abra R/executar.R e clique em "Source"
# Console:
source("caminho/para/tcc-value-relevance-setor-eletrico/R/executar.R")
```

As saídas vão para `resultados/r/`. O andamento aparece no console e fica em `resultados/r/log_execucao.txt`; no fim, o caminho do relatório em PDF é exibido. Uma diferença na conferência não impede o relatório; uma falha nas etapas 1 a 3, sim. Sem suporte a cairo (por exemplo, macOS sem XQuartz), o relatório é gerado com `pdf()` e símbolos equivalentes.

## Módulos (na ordem do pipeline)

| Arquivo | Etapa do TCC | Funções principais |
|---|---|---|
| `executar.R` | executa as cinco etapas, com log e resumo | — |
| `config.R` | parâmetros do estudo e utilitários de leitura e escrita | `ler`, `gravar`, `verdade`, `para_json` |
| `entradas.R` | fontes de dados | `carregar_entradas`, `lucro_individual`, `aplicacoes_financeiras` |
| `capitalizacao.R` | eq. (1) e conciliação acionária | `calcular_capitalizacao`, `quantidades_dfp`, `quantidades_fre`, `quantidades_por_classe`, `aplicar_cpfl` |
| `contabil.R` | eqs. (3)–(6) e conciliação do lucro | `montar_financeiro`, `conciliar_lucro` |
| `painel.R` | eq. (2), defasagem, filtros, winsorização, funil | `decisoes_amostra`, `montar_painel`, `winsorizar`, `funil_amostra` |
| `estimacao.R` | eq. (7), CR1, WCR, Driscoll–Kraay, Holm, R², VIF, FWL | `estimar`, `wild_cluster_restrito`, `driscoll_kraay`, `holm`, `vif_intra`, `fracao_fwl` |
| `especificacoes.R` | Tabelas 7 e 8; Apêndice C | `painel_completo`, `painel_contemporaneo`, `catalogo_modelos`, `estimar_todos` |
| `tabelas.R` | Tabelas 1–8, Apêndices A, B e C, Figura 1; eq. (8) | `gerar_tabelas`, `tabelas_descritivas`, `elegibilidade`, `desenhar_painel_figura1` |
| `valores.R` | números citados no TCC | `valor`, `formatar` |
| `conferencia.R` | Apêndice B (reprodução) | `conferir` |
| `relatorio.R` | relatório em PDF | `gerar_relatorio` |

## Usando as funções diretamente

```r
RAIZ <- "caminho/para/tcc-value-relevance-setor-eletrico"
for (m in c("config", "estimacao", "painel")) source(file.path(RAIZ, "R", paste0(m, ".R")), encoding = "UTF-8")
painel <- ler(file.path(RESULTADOS, "painel_principal.csv"))   # gerado pela etapa 1
r <- estimar(painel, "principal")                              # eq. (7) com CR1, WCR e Driscoll–Kraay
r$coefs[, c("variavel", "coef", "se_CR1", "p_CR1", "p_WCR", "excedencias")]
```

Para estimar sem uma empresa: `estimar(painel[painel$ticker != "CEBR3", ], "sem_CEB")`.
