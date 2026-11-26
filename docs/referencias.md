# Referências

Formato e conteúdo iguais aos do TCC. A coluna "Onde" indica o módulo ou a etapa em que cada referência fundamenta uma decisão do código. As referências marcadas com **(complementar)** não constam do TCC: são os trabalhos originais de técnicas usadas na implementação, citados nos comentários do código.

## Relevância informacional e avaliação

| Referência | Onde |
|---|---|
| Barth, M.E.; Beaver, W.H.; Landsman, W.R. 2001. The relevance of the value relevance literature for financial accounting standard setting: another view. Journal of Accounting and Economics 31(1–3): 77–104. DOI: 10.1016/S0165-4101(01)00019-2. | desenho do estudo; `capitalizacao` |
| Collins, D.W.; Maydew, E.L.; Weiss, I.S. 1997. Changes in the value-relevance of earnings and book values over the past forty years. Journal of Accounting and Economics 24(1): 39–67. DOI: 10.1016/S0165-4101(97)00015-3. | desenho do estudo; `capitalizacao` |
| Easton, P.D.; Harris, T.S. 1991. Earnings as an explanatory variable for returns. Journal of Accounting Research 29(1): 19–36. DOI: 10.2307/2491026. | capitalização × retorno (`capitalizacao`) |
| Kothari, S.P.; Zimmerman, J.L. 1995. Price and return models. Journal of Accounting and Economics 20(2): 155–192. DOI: 10.1016/0165-4101(95)00399-4. | capitalização × retorno (`capitalizacao`) |
| Ohlson, J.A. 1995. Earnings, book values, and dividends in equity valuation. Contemporary Accounting Research 11(2): 661–687. DOI: 10.1111/j.1911-3846.1995.tb00461.x. | ROE e PL (`contabil`); modelo em níveis e ln(PL) (`especificacoes`) |
| Penman, S.H. 2013. Financial Statement Analysis and Security Valuation. 5ed. McGraw-Hill, New York, NY, EUA. | escolha dos três fundamentos (`contabil`) |
| Souza, P.V.S.; Ribeiro, J.P.M.; Paulo, E. 2024. Organizational complexity and value relevance under the regulatory and financial standards of Brazilian electric power companies. Energy Policy 186: 114000. DOI: 10.1016/j.enpol.2024.114000. | estudo empírico mais próximo (setor elétrico) |
| Leite, J.P.P.C.; Novais, F.M.O.; Rossetti, N.; Carvalho, F.L. 2025. The relationship between accounting information quality and market value in Brazilian companies. Revista Brasileira de Gestão de Negócios 27(3): e20240213. DOI: 10.7819/rbgn.v27i03.4309. | comparação de resultados |

## Dados em painel e inferência

| Referência | Onde |
|---|---|
| Wooldridge, J.M. 2019. Introductory Econometrics: A Modern Approach. 7ed. Cengage, Boston, MA, EUA. | efeitos fixos, LSDV (`estimacao`); mínimo de quatro anos (`painel`) |
| Hsiao, C. 2022. Analysis of Panel Data. 4ed. Cambridge University Press, Cambridge, Reino Unido. | efeitos fixos (`estimacao`; `painel`) |
| Cameron, A.C.; Miller, D.L. 2015. A practitioner's guide to cluster-robust inference. Journal of Human Resources 50(2): 317–372. DOI: 10.3368/jhr.50.2.317. | CR1 (`estimacao`) |
| MacKinnon, J.G.; Nielsen, M.Ø.; Webb, M.D. 2023. Cluster-robust inference: a guide to empirical practice. Journal of Econometrics 232(2): 272–299. DOI: 10.1016/j.jeconom.2022.04.001. | CR1 com poucos grupos; não escolher o menor p (`estimacao`; `especificacoes`) |
| Cameron, A.C.; Gelbach, J.B.; Miller, D.L. 2008. Bootstrap-based improvements for inference with clustered errors. Review of Economics and Statistics 90(3): 414–427. DOI: 10.1162/rest.90.3.414. | WCR (`estimacao`) |
| Roodman, D.; MacKinnon, J.G.; Nielsen, M.Ø.; Webb, M.D. 2019. Fast and wild: Bootstrap inference in Stata using boottest. Stata Journal 19(1): 4–60. DOI: 10.1177/1536867X19830877. | WCR por enumeração (`estimacao`) |
| Holm, S. 1979. A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics 6(2): 65–70. | ajuste de Holm (`estimacao`) |
| Driscoll, J.C.; Kraay, A.C. 1998. Consistent covariance matrix estimation with spatially dependent panel data. Review of Economics and Statistics 80(4): 549–560. DOI: 10.1162/003465398557825. | Driscoll–Kraay (`estimacao`) |
| Hoechle, D. 2007. Robust standard errors for panel regressions with cross-sectional dependence. Stata Journal 7(3): 281–312. DOI: 10.1177/1536867X0700700301. | Driscoll–Kraay (`estimacao`) |
| Newey, W.K.; West, K.D. 1987. A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. Econometrica 55(3): 703–708. DOI: 10.2307/1913610. **(complementar)** | pesos de Bartlett no Driscoll–Kraay (`estimacao`) |
| Frisch, R.; Waugh, F.V. 1933. Partial time regressions as compared with individual trends. Econometrica 1(4): 387–401. DOI: 10.2307/1907330. **(complementar)** | concentração da variação (`estimacao`) |
| Lovell, M.C. 1963. Seasonal adjustment of economic time series and multiple regression analysis. Journal of the American Statistical Association 58(304): 993–1010. DOI: 10.1080/01621459.1963.10480682. **(complementar)** | concentração da variação (`estimacao`) |
| Hyndman, R.J.; Fan, Y. 1996. Sample quantiles in statistical packages. The American Statistician 50(4): 361–365. DOI: 10.1080/00031305.1996.10473566. **(complementar)** | quantil usado na winsorização (`painel`) |

## Normas e regulação

| Referência | Onde |
|---|---|
| Comitê de Pronunciamentos Contábeis [CPC]. 2010. Pronunciamento Técnico CPC 03 (R2): Demonstração dos fluxos de caixa. | caixa e equivalentes na dívida ampliada (`especificacoes`) |
| Brasil. 2013. Lei nº 12.783, de 11 de janeiro de 2013. Diário Oficial da União, Brasília, 14 jan. 2013. Seção 1, p. 1. | contexto setorial |
| Agência Nacional de Energia Elétrica [ANEEL]. 2026. Bandeiras tarifárias. Portal de Dados Abertos. | contexto setorial |
| Banco Central do Brasil. 2021. Comunicado nº 36.902, de 17 de março de 2021. | contexto (Selic) |

## Fontes de dados

| Referência | Onde |
|---|---|
| Comissão de Valores Mobiliários [CVM]. 2026a. Companhias abertas: Demonstrações Financeiras Padronizadas (DFP). Portal de Dados Abertos. Disponível em: <https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp>. | `dados/cvm`, `dados/cvm_complementar` |
| Comissão de Valores Mobiliários [CVM]. 2026b. Companhias abertas: Formulário de Referência (FRE). Portal de Dados Abertos. Disponível em: <https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre>. | `dados/cvm` |
| Brasil, Bolsa, Balcão [B3]. 2026. Cotações históricas do mercado à vista. Disponível em: <https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/>. | `dados/b3` |

## Documentos societários

| Referência | Onde |
|---|---|
| Cemig – Companhia Energética de Minas Gerais. 2021. Demonstrações financeiras de 2020. Nota 26: capital social. Disponível em: <https://www.sec.gov/Archives/edgar/data/1157557/000129281421002572/cig20210608_6k.htm>. | `config` (`CEMIG_2020`) |
| CPFL Energia S.A. 2013, 2015, 2016, 2017, 2018, 2019, 2020. Demonstrações financeiras de 2012 e de 2014 a 2019. Formulário 6-K. URLs em `dados/documentos/capital_cpfl_documentado.csv`. | `capitalizacao` (`aplicar_cpfl`) |
| EDP Energias do Brasil S.A. 2012. Demonstrações financeiras de 2011. Nota 26: patrimônio líquido. Disponível em: <https://www.edp.com/sites/default/files/document/2025-04/dfs_2011.pdf>. | `config` (`EDP_2010_2011`) |
| Companhia Energética de Brasília [CEB]. 2022. Demonstrações financeiras padronizadas de 2021, versão 2. | janela da CEB (`config.TRANSICOES`) |
| Auren Energia. 2025. Relatório anual 2024. | janela da Auren (`config.TRANSICOES`) |
| Light. 2023. Ata da Assembleia Geral Extraordinária realizada em 07 de junho de 2023. | janela da Light (`config.TRANSICOES`) |
| Light. 2024. Demonstrações financeiras de 2023. Notas explicativas 1 e 2. | caracterização da Light |
| Neoenergia. 2025. Relatório integrado 2024. | agrupamento societário (`config.GRUPOS_SOCIETARIOS`) |
| Taesa. 2025. Formulário de referência 2025. Versão 2. | agrupamento societário; IFRS 15 |
| Eneva. 2024. Relato integrado 2023. | caracterização da Eneva |
| Eletrobras. 2023. Relatório anual 2022: resumo executivo. | contexto setorial |
