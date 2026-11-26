# Metodologia

Este documento descreve cada etapa da análise com as equações e a notação do TCC e indica onde cada uma está implementada nas duas linguagens. As referências completas estão em [referencias.md](referencias.md).

## Sumário

1. [Desenho da pesquisa](#1-desenho-da-pesquisa)
2. [Dados e seleção dos documentos](#2-dados-e-seleção-dos-documentos)
3. [Capitalização de mercado (eqs. 1 e 2)](#3-capitalização-de-mercado-eqs-1-e-2)
4. [Fundamentos contábeis (eqs. 3 a 6)](#4-fundamentos-contábeis-eqs-3-a-6)
5. [Painéis](#5-painéis)
6. [Modelo e interpretação (eqs. 7 e 8)](#6-modelo-e-interpretação-eqs-7-e-8)
7. [Inferência](#7-inferência)
8. [Diagnósticos](#8-diagnósticos)
9. [Especificações alternativas e sensibilidades](#9-especificações-alternativas-e-sensibilidades)
10. [Correspondência código ↔ TCC](#10-correspondência-código--tcc)

---

## 1. Desenho da pesquisa

Pesquisa quantitativa, documental e associativa. A unidade de observação é a **empresa-ano**. O estudo se insere na literatura de **relevância informacional** (*value relevance*), que examina a associação entre números contábeis e valor de mercado (Barth, Beaver e Landsman, 2001). Ohlson (1995) relaciona valor, patrimônio, lucro e dividendos; Collins, Maydew e Weiss (1997) distinguem as contribuições do lucro e do patrimônio. A variável explicada é a **capitalização de mercado** (valor das ações), e não o retorno do acionista, que depende também do preço inicial e dos proventos (Easton e Harris, 1991; Kothari e Zimmerman, 1995). No setor elétrico, Souza, Ribeiro e Paulo (2024) e Leite et al. (2025) são os trabalhos empíricos mais próximos.

## 2. Dados e seleção dos documentos

| Fonte | Conteúdo usado | Referência |
|---|---|---|
| CVM, DFP | 11 contas contábeis e a composição do capital (ações emitidas e em tesouraria) | CVM (2026a) |
| CVM, FRE | capital social, subclasses de preferenciais, desdobramentos e grupamentos, tesouraria | CVM (2026b) |
| B3, COTAHIST | último negócio de dezembro de cada classe, em preço nominal | B3 (2026) |
| Documentos originais | Cemig 2020 (nota 26), CPFL 2012 e 2014–2019 (6-K na SEC), EDP 2010–2011 (DF de 2011, nota 26) | Cemig (2021); CPFL Energia (2013–2020); EDP (2012) |

Regras de seleção: exercícios encerrados em dezembro; registros do exercício corrente de cada DFP (não a coluna comparativa); **última versão** de cada documento; valores convertidos para reais; demonstração **consolidada** como regra (individual apenas nas quatro observações da Elektro).

## 3. Capitalização de mercado (eqs. 1 e 2)

$$\mathrm{VM}_{it} = \sum_{c=1}^{C_{it}} P_{ict}\,\bigl(Q_{ict} - T_{ict}\bigr) \tag{1}$$

$P$: última cotação nominal de dezembro da classe $c$; $Q$: quantidade emitida; $T$: quantidade em tesouraria. Ações de controladores e em circulação (*free float*) entram; ações em tesouraria não. A dívida não é somada.

$$y_{it} = \ln(\mathrm{VM}_{it}) \tag{2}$$

O logaritmo transforma diferenças de escala em diferenças proporcionais e reduz a assimetria entre empresas grandes e pequenas.

**Regras de conciliação** (`capitalizacao.py` / `capitalizacao.R`). Preço e quantidade vêm de fontes diferentes; os problemas abaixo alteram o valor sem nenhum aviso. Divergência não resolvida exclui a observação; nada é estimado ou extrapolado.

| Problema | Regra | Caso |
|---|---|---|
| Escala documental | Testa a quantidade da DFP em unidades e ×1000; vale a escala que coincide com o FRE no ano (ou, se o ano for ambíguo, a única escala confirmada para a empresa) | Rio Paranapanema ×1000 em 2020–2022 |
| Tesouraria já descontada | Se o FRE só coincide com "emitidas + tesouraria", recupera a quantidade emitida | Neoenergia 2021–2023 |
| Evento após dezembro | Desdobramento ou grupamento aprovado entre 31/12 e 30/06 seguinte, já refletido na DFP, é desfeito | Copel 2020 |
| Tesouraria divergente | Saldo final do FRE diferente do da DFP: exclui | Equatorial 2020, EDP |
| Subclasses PNA/PNB | Exige uma única repartição documentada no FRE | Copel e Eletrobras (só 2 anos) |
| Preço | Último negócio de dezembro da **mesma** classe; nunca a cotação de outra classe | — |
| Mudança de código | Usa a raiz antiga do ticker | Tractebel (TBLE) até 2015; MPX (MPXE) até 2012 |
| Documentos originais | Substituem a quantidade quando a base da CVM não concilia | Cemig 2020; CPFL; EDP |

Cada empresa-ano recebe um `status` em `resultados/<linguagem>/capitalizacao.csv` (ver [decisoes.md](decisoes.md)).

## 4. Fundamentos contábeis (eqs. 3 a 6)

$$\mathrm{ROE}_{it} = \frac{LL_{it}}{PL_{it}} \tag{3}$$

$LL$: lucro atribuível à controladora (conta 3.11.01 no consolidado); $PL$: patrimônio da controladora no encerramento (2.03 − 2.03.09). Exige $PL > 0$. No consolidado, numerador e denominador pertencem aos mesmos proprietários.

$$\mathrm{EBITDA}_{it} = \mathrm{EBIT}_{it} + |DA_{it}| \tag{4}$$

$\mathrm{EBIT}$: resultado antes do financeiro e dos tributos (3.05); $DA$: depreciação, amortização e exaustão da DVA (7.04.01). É uma aproximação: não reproduz EBITDA ajustado, regulatório ou geração de caixa.

$$\mathrm{AL}_{it} = \frac{DCP_{it} + DLP_{it} - CX_{it}}{\mathrm{EBITDA}_{it}} \tag{5}$$

$DCP$, $DLP$: empréstimos e financiamentos de curto (2.01.04) e longo prazo (2.02.01); $CX$: caixa e equivalentes (1.01.01). Exige EBITDA positivo; preserva posições líquidas de caixa ($AL < 0$).

$$\mathrm{PORTE}_{it} = \ln(AT_{it}) \tag{6}$$

$AT$: ativo total (conta 1). Com o valor também em logaritmo, o coeficiente é uma elasticidade.

**Conciliação do lucro.** Quando lucro total (3.11) ≠ controladora (3.11.01) + não controladores (3.11.02), com diferença acima de R$ 1 mil, consulta-se a DRE individual. Se ela for igual ao total consolidado e não houver não controladores, esse valor é o lucro da controladora (Light 2021–2024; Serena 2021). Caso contrário, o lucro fica ausente.

Rentabilidade, alavancagem e porte representam dimensões distintas (Penman, 2013); patrimônio e lucro são os elementos contábeis do modelo de Ohlson (1995).

## 5. Painéis

1. **Defasagem.** A capitalização de dezembro de $t$ é ligada aos fundamentos de $t-1$ (as DFPs anuais são divulgadas depois de dezembro).
2. **Elegibilidade.** Capitalização conciliada e os três fundamentos válidos. Valores ausentes não são preenchidos.
3. **Cobertura mínima.** Pelo menos quatro exercícios por empresa: com efeitos fixos de empresa, só a variação dentro da empresa identifica os coeficientes (Wooldridge, 2019; Hsiao, 2022).
4. **Comparação transversal.** Anos com uma só empresa são excluídos (2010–2011 na extensão histórica).
5. **Winsorização.** ROE e alavancagem nos percentis 1 e 99 de cada painel (quantil com interpolação linear, tipo 7 de Hyndman e Fan, 1996). Porte e capitalização não são winsorizados. Nas retiradas de empresas e nas janelas, os limites do painel principal permanecem fixos; as medidas alternativas e a extensão histórica usam limites da própria amostra.

| | Combinações | Capitalização conciliada | Três fundamentos | Mínimo de 4 anos |
|---|---:|---:|---:|---:|
| Painel principal (2020–2025) | 138 | 90 | 84 | **76** (14 empresas) |

Painel histórico (2012–2025): 97 observações de 15 empresas.

## 6. Modelo e interpretação (eqs. 7 e 8)

$$y_{it} = \alpha_i + \lambda_t + \beta_1\,\mathrm{ROE}_{i,t-1} + \beta_2\,\mathrm{AL}_{i,t-1} + \beta_3\,\mathrm{PORTE}_{i,t-1} + \varepsilon_{it} \tag{7}$$

$\alpha_i$: componente próprio da empresa; $\lambda_t$: componente comum ao ano; $\varepsilon_{it}$: parte não explicada. Estimação por mínimos quadrados com variáveis indicadoras (LSDV), uma categoria de referência em cada fator (Wooldridge, 2019; Hsiao, 2022). No painel principal, $K = 22$ parâmetros: constante, 13 indicadoras de empresa, 5 de ano e 3 fundamentos; $N - K = 54$ graus de liberdade residuais.

$$\Delta\%\mathrm{VM} = 100\,\bigl[\exp(\beta\,\Delta x) - 1\bigr] \tag{8}$$

ROE em decimal: +10 p.p. ⇒ $\Delta x = 0{,}10$ ⇒ −6,16%. Alavancagem: +1 vez ⇒ $\Delta x = 1$ ⇒ −9,62%. Porte (log-log): $1{,}10^{\beta_3} - 1$ ⇒ +5,04% para +10% de ativo.

## 7. Inferência

Seja $X$ a matriz completa (efeitos fixos e fundamentos), $P = (X'X)^{-1}X'$, $\hat\beta = Py$, $\hat\varepsilon = y - X\hat\beta$ e $g$ o grupo de cada observação ($G$ grupos).

**CR1** (Cameron e Miller, 2015; MacKinnon, Nielsen e Webb, 2023):

$$\widehat{V}_{\mathrm{CR1}} = \frac{G}{G-1}\,\frac{N-1}{N-K}\;\sum_{g=1}^{G} \bigl(P_g\,\hat\varepsilon_g\bigr)\bigl(P_g\,\hat\varepsilon_g\bigr)', \qquad t \sim t(G-1).$$

Com $G = 14$, a distribuição de referência é $t(13)$. Os intervalos de 95% das Tabelas 5 e da Figura 1 são CR1.

**WCR — wild cluster restricted bootstrap** (Cameron, Gelbach e Miller, 2008; Roodman et al., 2019). Para $H_0\!:\beta_j = 0$:

1. estima-se o modelo **sem** o fundamento $j$ (hipótese nula imposta): ajustados $\tilde f$ e resíduos restritos $\tilde u$;
2. para cada vetor de sinais $s \in \{-1,+1\}^G$ (Rademacher, o mesmo sinal para todas as observações do grupo), $y^{*} = \tilde f + s_g\,\tilde u$;
3. reestima-se o modelo completo em $y^{*}$ e calcula-se $t^{*}_j$ com o mesmo CR1;
4. $p_{\mathrm{WCR}} = \#\{\,|t^{*}_j| \ge |t_j|\,\} / 2^G$.

As **2^G combinações são todas enumeradas** (16.384 com 14 empresas; 4.096 com 12 grupos societários): não há sorteio, e o valor de p é exatamente reprodutível. Não há ajuste adicional de resíduos por alavancagem estatística. O WCR recebeu maior peso na avaliação; divergências entre CR1 e WCR foram apresentadas sem escolher o menor p (MacKinnon, Nielsen e Webb, 2023).

**Holm** (Holm, 1979), aplicado apenas às três hipóteses do modelo principal: ordenam-se os p WCR e multiplicam-se por 3, 2 e 1, com ajuste monotônico. Resultado: 0,0077 (ROE), 0,0259 (alavancagem) e 0,0122 (porte).

**Driscoll–Kraay** (Driscoll e Kraay, 1998; Hoechle, 2007), comparação suplementar (Apêndice C, Tabela 4). Com $\tilde X$ = fundamentos sem os efeitos fixos e $h_t = \sum_i \tilde x_{it}\hat\varepsilon_{it}$,

$$\widehat S = \sum_t h_t h_t' + \sum_{\ell=1}^{L} w_\ell \sum_t \bigl(h_t h_{t-\ell}' + h_{t-\ell} h_t'\bigr), \quad w_\ell = 1 - \frac{\ell}{L+1}, \qquad \widehat V_{\mathrm{DK}} = (\tilde X'\tilde X)^{-1}\,\widehat S\,(\tilde X'\tilde X)^{-1}\,\frac{N}{N-K},$$

com pesos de Bartlett (Newey e West, 1987), $L \in \{1, 2\}$ e $t(N-K)$. A fundamentação assintótica em uma dimensão temporal longa limita a interpretação num painel de seis anos.

## 8. Diagnósticos

| Medida | Definição | Principal |
|---|---|---:|
| R² global | $1 - \mathrm{SQR}/\mathrm{SQT}$, incluindo os efeitos fixos | 0,9711 |
| R² intra-grupo | dados centrados por empresa, coeficientes do modelo de duas vias (convenção do PanelOLS) | 0,2130 |
| R² parcial de duas vias | modelo completo × modelo só com efeitos fixos | 0,2896 |
| VIF intra | diagonal da inversa da correlação dos fundamentos após retirar os efeitos fixos | 1,02; 1,36; 1,35 |
| Concentração (FWL) | $z_i^2/\sum z^2$, com $z$ = fundamento sem efeitos fixos e sem os outros fundamentos (Frisch e Waugh, 1933; Lovell, 1963) | CEB: 54,55% do ROE; CEB-2022: 31,38% |

A concentração mostra de onde vem a informação que identifica o coeficiente; não é contribuição causal.

## 9. Especificações alternativas e sensibilidades

Cada especificação responde a uma pergunta econômica definida antes de olhar o valor de p. Só o modelo principal recebe Holm; as demais são exploratórias.

| Modelo (`coeficientes.csv`) | Pergunta | N/G/K | Tabela do TCC |
|---|---|---|---|
| `principal` | Associação dos três fundamentos | 76/14/22 | 5, 6, 7; Ap. C 4 |
| `sem_winsor` | A winsorização criou o sinal? | 76/14/22 | 7 |
| `excluir_<ticker>` (14) | Uma empresa determina o resultado? | 70–72/13/21 | 7; Figura 1; Ap. C 1 |
| `sem_EKTR_TAEE` | Empresas com vínculo societário | 66/12/20 | 7 |
| `balanceado` | Só empresas com os seis anos | 54/9/17 | 7; Ap. C 2 |
| `cotacoes_desde_dia20` | Último negócio a partir de 20/dez (liquidez) | 73/14/22 | 7 |
| `historico`, `historico_mesmas_empresas` | Extensão 2012–2025 | 97/15/31; 89/14/30 | 7 |
| `controle_PL` | + ln(PL da controladora) | 76/14/23 | 7, 8 |
| `ROA`, `ROA_operacional` | Lucro total/ativo; EBIT/ativo no lugar do ROE | 76/14/22 | 7, 8 |
| `lucro_PL_niveis` | Capitalização, lucro e PL em R$ bilhões (inspirado em Ohlson, 1995) | 76/14/21 | 8 |
| `divida_ampla` | Dívida líquida também das aplicações financeiras (1.01.02; CPC, 2010) | 76/14/22 | 7, 8 |
| `sem_CEB_2022`, `sem_CEB_2021_2022` | Mercado de 2022 (ou 2021–2022) da CEB, após a venda da CEB-D | 75/14/22; 74/14/22 | 7; Ap. C 2 |
| `sem_transicoes` | Sem CEB 2021–22, Auren 2022–25 e Light 2023–24 | 69/13/21 | 7; Ap. C 2 |
| `contemporaneo`, `defasado_amostra_contemporanea` | Fundamentos do mesmo ano (retrospectivo) e o defasado nas mesmas linhas | 73/14/22 | Ap. C 3 |
| `ROE_media3`, `defasado_amostra_media3` | Média de três ROEs anteriores, escopo constante | 74/14/22 | Ap. C 3 |
| `ROE_PLmedio`, `defasado_amostra_PLmedio` | Lucro / média do PL inicial e final | 75/14/22 | Ap. C 3 |
| `grupos_societarios` | 12 grupos de inferência (Elektro–Neoenergia; Taesa–Cemig) | 76/12/22 | Ap. C 3 |
| `somente_consolidadas` | Sem as 4 observações individuais da Elektro | 72/13/21 | Ap. C 3 |
| `sem_CEB_<ano>`, `sem_CEB_2020_2022`, `ROA_sem_CEB` | Diagnósticos adicionais (não tabelados no texto) | — | — |

## 10. Correspondência código ↔ TCC

| No TCC | Python (`python/tcc/`) | R (`R/`) |
|---|---|---|
| Parâmetros do estudo | `config.py` | `config.R` |
| Fontes de dados | `entradas.py` | `entradas.R` |
| Eq. (1), conciliação acionária | `capitalizacao.py` → `calcular` | `capitalizacao.R` → `calcular_capitalizacao` |
| Eqs. (3)–(6), conciliação do lucro | `contabil.py` → `montar`, `conciliar_lucro` | `contabil.R` → `montar_financeiro`, `conciliar_lucro` |
| Eq. (2), defasagem, filtros, winsorização, funil | `painel.py` | `painel.R` |
| Eq. (7), CR1, WCR, DK, Holm, R², VIF, FWL | `estimacao.py` | `estimacao.R` |
| Especificações alternativas (Tabelas 7, 8; Ap. C) | `especificacoes.py` | `especificacoes.R` |
| Tabelas 1, 4–8, Ap. C, Figura 1; eq. (8) | `tabelas.py` | `tabelas.R` |
| Números citados no texto | `valores.py` | `valores.R` |
| Apêndice B (reprodução) | `conferencia.py` | `conferencia.R` |
| Relatório em PDF | `relatorio.py` | `relatorio.R` |
