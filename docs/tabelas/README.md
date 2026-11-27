# Tabelas e figura do TCC

Esta pasta tem as **15 tabelas** e a **Figura 1** do TCC, como o código as gera. Clique num arquivo `.csv` e o GitHub o mostra como tabela.

- **Formato.** Os números estão com ponto decimal, porque é CSV; o relatório em PDF converte para vírgula. O arredondamento é o mesmo do TCC. Na Tabela 7, "*" marca p WCR < 0,05, decidido antes do arredondamento.
- **Origem.** Os arquivos são cópias de `resultados/python/tabelas_tcc/`. A versão em R gera arquivos idênticos.
- **Atualização.** A integração contínua confere, a cada envio, que esta cópia continua igual ao que o código gera (`scripts/conferir_tabelas_publicadas.py`).
- **Versão formatada.** As mesmas tabelas, com explicação, estão no [relatório de reprodução em PDF](../relatorio_reproducao.pdf).

## Corpo do texto

| No TCC | Arquivo | O que mostra |
|---|---|---|
| Tabela 1. Cobertura anual dos painéis | [tabela_1_cobertura.csv](tabela_1_cobertura.csv) | Empresas por ano no painel principal (2020–2025) e na extensão histórica; totais de 76 e 97 observações |
| Tabela 2. Etapas de construção e verificação | [tabela_2_etapas.csv](tabela_2_etapas.csv) | As seis etapas e o módulo do código que executa cada uma |
| Tabela 3. Definição e unidade das variáveis | [tabela_3_variaveis.csv](tabela_3_variaveis.csv) | Medida, definição, unidade, equação e nome da coluna no painel |
| Tabela 4. Estatísticas descritivas | [tabela_4_descritivas.csv](tabela_4_descritivas.csv) | Média, desvio-padrão, mínimo, mediana e máximo das cinco variáveis |
| Tabela 5. Coeficientes e inferência agrupada | [tabela_5_coeficientes.csv](tabela_5_coeficientes.csv) | Coeficientes do modelo principal, erro-padrão CR1, p e intervalo de 95% |
| Tabela 6. Valores de p CR1 e WCR | [tabela_6_cr1_wcr_holm.csv](tabela_6_cr1_wcr_holm.csv) | p CR1, p WCR e p de Holm, com as contagens exatas do bootstrap (de 16.384 combinações) |
| Eq. (8), citada no texto | [interpretacao_efeitos.csv](interpretacao_efeitos.csv) | Os coeficientes convertidos em variação % da capitalização: −6,16%, −9,62% e +5,04% |
| Tabela 7. Matriz de sensibilidade | [tabela_7_sensibilidade.csv](tabela_7_sensibilidade.csv) | p WCR dos três fundamentos nas 18 verificações |
| Figura 1. Coeficientes após a retirada de cada empresa | [figura_1.png](../figura_1.png) | Coeficiente e intervalo de 95% sem cada uma das 14 empresas; destaque para a CEB |
| Tabela 8. Especificações alternativas | [tabela_8_especificacoes.csv](tabela_8_especificacoes.csv) | ln(PL), ROA líquido, ROA operacional, lucro e PL em níveis, dívida ampliada |

## Apêndices

| No TCC | Arquivo | O que mostra |
|---|---|---|
| Apêndice A, Tabela 1. Companhias do painel principal | [apA_tabela_1_companhias.csv](apA_tabela_1_companhias.csv) | As 14 companhias, com o N recalculado do painel, o segmento e a relação societária |
| Apêndice A, Tabela 2. Companhias fora do painel | [apA_tabela_2_fora_do_painel.csv](apA_tabela_2_fora_do_painel.csv) | As 9 emissoras excluídas: anos elegíveis, motivos registrados pelo código e restrição escrita no TCC |
| Apêndice B, Tabela 1. Rubricas contábeis | [apB_tabela_1_rubricas.csv](apB_tabela_1_rubricas.csv) | As 12 contas da CVM usadas, com demonstração e código |
| Apêndice C, Tabela 1. Retirada individual das 14 empresas | [apC_tabela_1_retiradas.csv](apC_tabela_1_retiradas.csv) | Coeficientes e erros-padrão sem cada empresa (os números da Figura 1) |
| Apêndice C, Tabela 2. Painel balanceado e janelas de transição | [apC_tabela_2_balanceado_janelas.csv](apC_tabela_2_balanceado_janelas.csv) | Painel balanceado, sem CEB-2022, sem CEB 2021–22 e sem transições, com p CR1, WCR e DK1 |
| Apêndice C, Tabela 3. Alinhamento temporal, rentabilidade e agrupamento | [apC_tabela_3_alinhamento_agrupamento.csv](apC_tabela_3_alinhamento_agrupamento.csv) | Fundamentos do mesmo ano, ROE médio de três anos, ROE com PL médio, 12 grupos societários e só consolidadas |
| Apêndice C, Tabela 4. Driscoll–Kraay | [apC_tabela_4_driscoll_kraay.csv](apC_tabela_4_driscoll_kraay.csv) | p Driscoll–Kraay com uma e duas defasagens |

## Nomes das colunas

| Coluna | Significado |
|---|---|
| `p_CR1` | valor de p com erro-padrão agrupado por empresa, CR1 e t(G−1) |
| `p_WCR` | valor de p do *wild cluster restricted bootstrap*, com enumeração completa |
| `p_Holm` | p WCR ajustado por Holm para as três hipóteses |
| `p_DK1`, `p_DK2` | valor de p Driscoll–Kraay com uma e duas defasagens |
| `N_G_K` | observações / grupos / parâmetros |
| `R2_intra` | R² intra-grupo |
| `IC95_inf`, `IC95_sup` | limites do intervalo CR1 de 95% |
| `excedencias`, `combinacoes` | combinações de sinais com estatística tão ou mais extrema que a observada, e total de combinações |
