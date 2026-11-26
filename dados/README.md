# Dados

Extratos congelados na coleta (setembro de 2026). Nenhum script acessa a internet: as etapas partem destes arquivos. Os arquivos brutos de origem estão identificados por SHA-256 em `fontes.json` (DFP e FRE da CVM), `cvm_complementar/catalogo_*.json` e `b3/manifesto_precos.json` (COTAHIST da B3). Valores monetários estão em reais, exceto quando indicado.

## `cvm/` — Comissão de Valores Mobiliários

| Arquivo | Linhas | Conteúdo | Colunas usadas |
|---|---:|---|---|
| `universo_identificado.csv` | 23 | Listagem de trabalho: 23 emissoras | `ticker`, `CD_CVM` (código CVM), `CNPJ_CIA` (CNPJ conciliado). `observacoes_estimadas` e `CNPJ_original` são campos legados, não usados |
| `capital_dfp.csv` | 136 | Composição do capital na DFP | `CNPJ_CIA`, `ano`, `QT_ACAO_ORDIN_CAP_INTEGR` e `QT_ACAO_PREF_CAP_INTEGR` (emitidas), `QT_ACAO_ORDIN_TESOURO` e `QT_ACAO_PREF_TESOURO` (tesouraria) |
| `capital_social.csv` | 1.295 | Capital social no FRE | `CNPJ_Companhia`, `Tipo_Capital`, `Data_Autorizacao_Aprovacao`, `Quantidade_Acoes_Ordinarias`, `Quantidade_Acoes_Preferenciais`, `ID_Capital_Social`, `arquivo_ano` |
| `capital_social_classe_acao.csv` | 473 | Preferenciais por subclasse (PNA, PNB) | `ID_Capital_Social`, `arquivo_ano`, `Tipo_Classe_Acao_Preferencial`, `Quantidade_Acoes` |
| `capital_social_desdobramento.csv` | 102 | Desdobramentos e grupamentos | `CNPJ_Companhia`, `Data_Aprovacao`, `Tipo_Evento`, quantidades antes e depois |
| `valor_mobiliario_tesouraria_movimentacao.csv` | 115 | Movimentação de ações em tesouraria | `CNPJ_Companhia`, `Data_Fim_Exercicio_Social`, `Especie_Acao`, `Quantidade_Final` |
| `contas_cvm.csv` | 3.691 | 11 contas da DFP, exercício corrente, última versão, um escopo por empresa-ano | `CD_CVM`, `ano`, `escopo` (`con` consolidado, `ind` individual), `CD_CONTA`, `valor` (em reais) |

Contas em `contas_cvm.csv` (Apêndice B, Tabela 1 do TCC):

| Conta | Demonstração | Descrição |
|---|---|---|
| 1 | BPA | Ativo total |
| 1.01.01 | BPA | Caixa e equivalentes de caixa |
| 2.01.04 | BPP | Empréstimos e financiamentos de curto prazo |
| 2.02.01 | BPP | Empréstimos e financiamentos de longo prazo |
| 2.03 | BPP | Patrimônio líquido total |
| 2.03.09 | BPP | Participação dos não controladores |
| 3.05 | DRE | Resultado antes do resultado financeiro e dos tributos |
| 3.11 | DRE | Lucro líquido total |
| 3.11.01 | DRE | Lucro atribuído à controladora |
| 3.11.02 | DRE | Lucro atribuído aos não controladores |
| 7.04.01 | DVA | Depreciação, amortização e exaustão |

## `b3/` — B3

| Arquivo | Linhas | Conteúdo |
|---|---:|---|
| `precos_dezembro_2010_2025.csv` | 13.442 | Último negócio de dezembro de cada ticker do mercado à vista: `ticker`, `ano`, `data` (AAAAMMDD), `classe` (ex.: ON, PN, PNA, PNB), `preco` (nominal, por ação), `fator` (fator de cotação do arquivo), `negocios`, `isin` |
| `manifesto_precos.json` | — | Arquivo COTAHIST de origem de cada ano, com SHA-256, número de linhas e de tickers em dezembro |

## `documentos/` — documentos originais e valores do TCC

| Arquivo | Conteúdo |
|---|---|
| `capital_cpfl_documentado.csv` | CPFL, 2012 e 2014–2019: `ano`, `emitidas`, `tesouraria`, `url` (DF original no formulário 6-K da SEC) |
| `caracterizacao_empresas.csv` | As 14 empresas do painel: nome, código, N, segmento (G, T, D) e relação societária (Apêndice A, Tabela 1). O N é recalculado pelo código e conferido |
| `companhias_fora_painel_tcc.csv` | As 9 emissoras fora do painel e a restrição como descrita no TCC (Apêndice A, Tabela 2): `identificador`, `ticker`, `restricao_tcc` |
| `valores_publicados_tcc.csv` | Os 498 valores impressos no TCC: `tabela`, `linha`, `item`, `chave`, `decimais`, `tipo`, `publicado` (ver [docs/conferencia.md](../docs/conferencia.md)) |

## `cvm_complementar/` — extratos adicionais da DFP

| Arquivo | Conteúdo | Uso |
|---|---|---|
| `lucro_individual_2021.csv` … `_2024.csv` | Conta 3.11 da DRE individual da Light (CVM 19879) e da Serena (26441) | Conciliação do lucro da controladora |
| `complementos_2019.csv` … `_2024.csv` | BPA, BPP, DRE e DFC das 23 emissoras | Conta 1.01.02 (aplicações financeiras) na dívida ampliada |
| `catalogo_lucro.json`, `catalogo_complementos.json` | URL e SHA-256 de cada arquivo da CVM baixado | Rastreabilidade |

## `fontes.json`

URL e SHA-256 dos pacotes anuais da DFP (2010–2018) e do FRE (2010–2019) cujos hashes foram preservados na coleta original. Como registra o pacote original, os manifestos cobrem as extrações com hash preservado e não são um catálogo integral de cada arquivo bruto; os extratos complementares de 2019–2024 têm seus hashes em `cvm_complementar/catalogo_*.json`.
