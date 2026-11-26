# Conferência dos resultados

Cada execução termina com três conferências independentes (`conferencia.py` / `conferencia.R`). A execução informa **TUDO CONFERIDO** ou lista cada divergência.

## A. Pacote original

As saídas são comparadas com as do pacote que gerou o TCC (pasta `referencia/`, setembro de 2026).

| Item | Critério | Resultado |
|---|---|---|
| Capitalização, componentes, contas, decisões, painéis | Tabelas idênticas | idênticas |
| Coeficientes, CR1, p CR1, IC (37 modelos, 111 coeficientes) | Diferença relativa ≤ 10⁻⁸ | ≤ 10⁻¹³ |
| p WCR e **contagens de excedências** | Contagem exata (tolerância zero) | idênticas |
| Driscoll–Kraay (1 e 2 defasagens) | ≤ 10⁻⁸ | ≤ 10⁻¹³ |
| N, G, K, R² intra, R² parcial, R² global | ≤ 10⁻⁸ | ≤ 10⁻¹⁴ |
| Holm, VIF, frações FWL, influência por observação | ≤ 10⁻⁸ | ≤ 10⁻¹³ |

## B. Bibliotecas independentes

As fórmulas próprias (álgebra de matrizes) são comparadas com bibliotecas consolidadas, como declarado no TCC.

| Versão | Biblioteca | Itens | Diferença máxima |
|---|---|---|---|
| Python | statsmodels (OLS com indicadoras, `cov_type="cluster"`, t(G−1)) | coeficientes, CR1, p | 10⁻¹⁵ |
| Python | linearmodels (`PanelOLS`, efeitos de empresa e ano) | coeficientes, CR1, R² intra e global, Driscoll–Kraay | 10⁻¹⁴ |
| R | fixest (`feols`, `ssc(K.fixef = "full")`) | coeficientes, CR1, p, CR1 com 12 grupos | 10⁻¹⁰ (tolerância interna do fixest) |

## C. Texto do TCC

`dados/documentos/valores_publicados_tcc.csv` reúne os **498 valores impressos no TCC**: Tabelas 1 a 8, Apêndices A, B e C e 16 números citados no texto. As Tabelas 2 e 3 contribuem com os parâmetros que citam (mínimo de quatro anos; percentis 1 e 99), o Apêndice A com o N de cada companhia e os exercícios elegíveis de Copel e Eletrobras, e o Apêndice B com os 12 códigos de conta. Cada linha tem a chave do número (gramática em `valores.py` / `valores.R`), as casas decimais, o tipo de formatação e o valor como publicado. Antes de entrar no repositório, cada valor foi localizado no texto do TCC, na mesma ordem em que aparece nas tabelas.

A conferência recalcula cada valor, formata com as mesmas regras do texto (vírgula decimal, sinal "−", "< 0,0001", asterisco de p < 0,05 antes do arredondamento) e compara os textos.

| Origem | Valores | Coincidem |
|---|---:|---:|
| Tabela 1 | 14 | 14 |
| Tabela 2 | 1 | 1 |
| Tabela 3 | 2 | 2 |
| Tabela 4 | 25 | 25 |
| Tabela 5 | 15 | 15 |
| Tabela 6 | 6 | 6 |
| Tabela 7 | 90 | 90 |
| Tabela 8 | 45 | 45 |
| Apêndice A, Tabela 1 | 16 | 16 |
| Apêndice A, Tabela 2 | 2 | 2 |
| Apêndice B, Tabela 1 | 12 | 12 |
| Apêndice C, Tabela 1 | 112 | 112 |
| Apêndice C, Tabela 2 | 48 | 48 |
| Apêndice C, Tabela 3 | 88 | 88 |
| Apêndice C, Tabela 4 | 6 | 6 |
| Texto | 16 | 16 |
| **Total** | **498** | **498** |

Além dos valores, a conferência C faz três verificações que não cabem numa comparação de números:

- **Listas do Apêndice A.** As 14 companhias com observações no painel são exatamente as da Tabela 1 do Apêndice A, e as 9 sem nenhuma observação são exatamente as da Tabela 2.
- **Motivo da exclusão.** Cada uma dessas 9 tem menos de quatro exercícios elegíveis entre 2020 e 2025.
- **Rubricas do Apêndice B.** Um código só é aceito se a conta existe nos extratos da CVM, na demonstração indicada. Assim a tabela descreve as contas de fato usadas, e não só o texto do TCC.

As tabelas puramente descritivas (Tabelas 2 e 3, Apêndice A e Apêndice B) também são geradas pelo código, em `resultados/<linguagem>/tabelas_tcc/`. O texto delas vem de `config.py` / `config.R` e de `dados/documentos/`; os números e as listas de empresas vêm dos dados.

O resultado item a item fica em `resultados/<linguagem>/conferencia_tcc.csv` e no anexo do relatório em PDF.

## Equivalência entre as linguagens

Depois de rodar as duas versões, `python scripts/comparar_versoes.py` compara `resultados/python/` com `resultados/r/`, arquivo a arquivo: os 14 arquivos de resultados (valores numéricos com diferença relativa ≤ 10⁻⁹; na prática, da ordem de 10⁻¹³) e as 16 tabelas do TCC em CSV (idênticas, célula a célula). A integração contínua (`.github/workflows/reproducao.yml`) roda as duas versões e essa comparação a cada envio.
