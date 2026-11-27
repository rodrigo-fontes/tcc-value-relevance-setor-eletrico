# Decisões de projeto

Este documento registra **por que** o estudo e o repositório foram feitos como foram. Cada decisão traz:

- o que foi decidido;
- por que foi decidido assim;
- que alternativa existia e como ela foi tratada;
- onde a decisão aparece no TCC e no código.

As decisões metodológicas (parte A) seguem o texto do TCC. As de dados (parte B) resumem as regras; os casos concretos estão em [decisoes.md](decisoes.md). As de engenharia (parte C) são escolhas do pacote de reprodução e não alteram nenhum resultado do trabalho.

> **Como usar na defesa.** As perguntas "por que você fez assim?" quase sempre caem numa das decisões A1 a A19. A coluna "Alternativa" diz se a alternativa foi estimada e onde está o resultado.

## Sumário

| | Decisão | No TCC |
|---|---|---|
| **A** | **Metodologia** | |
| A1 | Empresa-ano como unidade de observação | Método |
| A2 | Capitalização de mercado, não retorno | Introdução; eqs. 1–2 |
| A3 | Logaritmo da capitalização | eq. 2 |
| A4 | Três fundamentos: rentabilidade, alavancagem e porte | Tabela 3 |
| A5 | Fundamentos do exercício anterior (t−1) | Fundamentos e defasagem |
| A6 | Lucro e patrimônio da controladora; consolidado como regra | Dados; eq. 3 |
| A7 | EBITDA aproximado pela DVA e denominadores positivos | eqs. 4–5 |
| A8 | Última versão de cada demonstração | Dados |
| A9 | Janela principal 2020–2025 e extensão histórica | Extensão histórica; Tabela 1 |
| A10 | Mínimo de quatro exercícios por empresa | Delimitação da amostra |
| A11 | Nenhum valor ausente preenchido | Delimitação; Extensão histórica |
| A12 | Winsorização de ROE e alavancagem nos percentis 1 e 99 | Fundamentos e defasagem |
| A13 | Efeitos fixos de empresa e de ano | eq. 7 |
| A14 | Erro-padrão CR1 com t(G−1) | Inferência |
| A15 | WCR com enumeração completa como teste prioritário | Inferência |
| A16 | Holm só para as três hipóteses | Critérios de interpretação |
| A17 | Driscoll–Kraay só como comparação suplementar | Inferência; Apêndice C |
| A18 | Sensibilidades como diagnósticos exploratórios | Tabelas 7–8; Apêndice C |
| A19 | Leitura como associação, convertida pela eq. 8 | eq. 8 |
| **B** | **Dados** | |
| B1 | Preço e quantidade da mesma classe | eq. 1 |
| B2 | Quantidade da DFP conferida com o FRE | Dados; Apêndice B |
| B3 | Documentos originais só quando a CVM não concilia | Dados |
| B4 | Conciliação do lucro da controladora | Dados |
| B5 | Listagem de 23 emissoras, sem pretensão de censo | Delimitação; Apêndice A |
| **C** | **Engenharia do pacote** | |
| C1 | Fórmulas próprias, conferidas com bibliotecas | Dados (software) |
| C2 | Duas implementações independentes: Python e R | — |
| C3 | Extratos congelados, sem acesso à internet | Apêndice B |
| C4 | Conferência com o texto impresso do TCC | Apêndice B |
| C5 | Parâmetros num único arquivo | — |
| C6 | Um roteiro de relatório para as duas linguagens | — |
| C7 | Resultados idênticos entre execuções | — |
| C8 | Integração contínua a cada envio | — |
| C9 | Um único ramo, com pastas `python/` e `R/` | — |
| C10 | Comentários linha a linha, com referências | — |
| C11 | Licenças separadas para código e texto | — |
| C12 | Cópia das tabelas geradas em `docs/tabelas/` | — |

---

## A. Metodologia

### A1. Empresa-ano como unidade de observação

- **Decisão.** Cada linha é uma companhia em um ano. Seis exercícios da mesma companhia formam seis registros.
- **Por quê.** Permite acompanhar a mesma empresa ao longo do tempo e separar o que é próprio dela do que muda entre anos.
- **Consequência.** Registros da mesma empresa são dependentes entre si, o que leva à inferência agrupada por empresa (A14 e A15).
- **Onde.** TCC, Método. Código: `painel.py` / `painel.R`.

### A2. Capitalização de mercado, não retorno

- **Decisão.** A variável explicada é o valor de mercado das ações em dezembro (eq. 1). A dívida não é somada.
- **Por quê.** O estudo é de relevância informacional em nível: associa valor a números contábeis (Barth, Beaver e Landsman, 2001). O retorno depende também do preço inicial e dos proventos (Easton e Harris, 1991; Kothari e Zimmerman, 1995).
- **Alternativa.** Capitalização, lucro e PL em R$ bilhões, numa forma inspirada em Ohlson (1995): Tabela 8, linha "Lucro e PL".
- **Onde.** TCC, eqs. 1–2. Código: `capitalizacao.py` / `capitalizacao.R`.

### A3. Logaritmo da capitalização

- **Decisão.** y = ln(VM).
- **Por quê.** Transforma diferenças de escala em diferenças proporcionais e reduz a assimetria entre empresas grandes e pequenas. Com o porte também em logaritmo, β₃ é uma elasticidade.
- **Onde.** TCC, eq. 2. Código: `painel.py` / `painel.R` (coluna `ln_mcap`).

### A4. Três fundamentos: rentabilidade, alavancagem e porte

- **Decisão.** O modelo tem três fundamentos: ROE, dívida líquida/EBITDA e ln(ativo).
- **Por quê.** Representam dimensões distintas: resultado sobre o capital, dívida sobre o resultado operacional e tamanho (Penman, 2013). Com 14 empresas, limitar o número de relações estimadas preserva graus de liberdade. O crescimento dos ativos não entrou no modelo principal.
- **Alternativas.** ln(PL), ROA líquido, ROA operacional e dívida ampliada (Tabelas 7 e 8); ROE médio de três anos e ROE com PL médio (Apêndice C, Tabela 3).
- **Onde.** TCC, Tabela 3. Código: `contabil.py` / `contabil.R`.

### A5. Fundamentos do exercício anterior (t−1)

- **Decisão.** A capitalização de dezembro de t é ligada aos fundamentos de t−1: dezembro de 2020 aos indicadores de 2019.
- **Por quê.** As DFPs anuais são divulgadas depois de dezembro. Os fundamentos do mesmo ano não eram informação disponível naquela data.
- **Alternativa.** Modelo contemporâneo, comparado com o defasado nas mesmas 73 observações (Apêndice C, Tabela 3). A versão contemporânea é retrospectiva.
- **Onde.** TCC, "Fundamentos contábeis e defasagem". Código: `painel.py` / `painel.R`.

### A6. Lucro e patrimônio da controladora; consolidado como regra

- **Decisão.** No consolidado, ROE = lucro atribuível à controladora (3.11.01) / PL da controladora (2.03 − 2.03.09). A Elektro entra pelo individual em quatro observações.
- **Por quê.** Numerador e denominador pertencem aos mesmos proprietários. Dividir o lucro dos acionistas da controladora pelo patrimônio total misturaria donos diferentes.
- **Alternativa.** Retirada das quatro observações individuais: "Só consolidadas" (Apêndice C, Tabela 3).
- **Onde.** TCC, Dados e eq. 3; Apêndice B, Tabela 1. Código: `contabil.py` / `contabil.R`.

### A7. EBITDA aproximado pela DVA e denominadores positivos

- **Decisão.** EBITDA = resultado antes do financeiro e dos tributos (3.05) + |depreciação e amortização da DVA (7.04.01)|. A alavancagem exige EBITDA positivo; o ROE exige PL positivo. Posições líquidas de caixa (AL < 0) são mantidas.
- **Por quê.** A DFP não traz EBITDA padronizado, e a DVA é a fonte comparável entre empresas. Com denominador negativo ou zero, o índice perde sentido econômico.
- **Consequência.** É uma aproximação: não reproduz EBITDA ajustado, regulatório ou geração de caixa. Light 2023 sai porque o EBITDA de 2022 foi negativo.
- **Onde.** TCC, eqs. 4–5. Código: `contabil.py` / `contabil.R`.

### A8. Última versão de cada demonstração

- **Decisão.** Usa-se a última versão disponível de cada DFP, só com o exercício corrente.
- **Por quê.** Incorpora as correções feitas pelas próprias empresas.
- **Consequência.** A base reconstrói o passado retrospectivamente, sem reproduzir exatamente a informação conhecida pelo investidor em cada data. O TCC registra isso como limite, que vale também para o modelo defasado.
- **Onde.** TCC, Dados. Código: `entradas.py` / `entradas.R`.

### A9. Janela principal 2020–2025 e extensão histórica

- **Decisão.** O painel principal cobre 2020–2025. A extensão histórica (2012–2025, 97 observações de 15 empresas) é uma verificação.
- **Por quê.** Antes de 2020, só duas ou três empresas contribuíam por ano. A janela recente tem a maior cobertura entre companhias. Em 2010–2011 só a EDP era elegível, o que não permite comparação transversal.
- **Alternativa.** Extensão histórica e extensão com as mesmas 14 empresas (Tabela 7).
- **Onde.** TCC, "Extensão histórica" e Tabela 1. Código: `config.py` (`ANO_INICIO_PRINCIPAL`, `MIN_EMPRESAS_ANO`).

### A10. Mínimo de quatro exercícios por empresa

- **Decisão.** Uma empresa só entra com pelo menos quatro exercícios elegíveis.
- **Por quê.** Com efeito fixo de empresa, só a variação dentro de cada empresa identifica os coeficientes. Uma empresa com um ou dois anos contribui com pouca ou nenhuma informação (Wooldridge, 2019; Hsiao, 2022).
- **Consequência.** O filtro retirou oito observações de cinco emissoras (84 → 76). Copel e Eletrobras ficaram fora com apenas dois exercícios elegíveis (Apêndice A, Tabela 2).
- **Alternativa.** Painel balanceado, só com quem tem os seis anos (Tabela 7; Apêndice C, Tabela 2).
- **Onde.** TCC, "Delimitação da amostra". Código: `config.py` (`MIN_EXERCICIOS`); `painel.py` / `painel.R`.

### A11. Nenhum valor ausente preenchido

- **Decisão.** Não há imputação nem extrapolação. Uma divergência não resolvida exclui a observação.
- **Por quê.** Um valor preenchido seria uma hipótese do pesquisador apresentada como dado. Nos documentos originais, os valores não foram estendidos a anos sem comprovação.
- **Consequência.** A amostra depende da disponibilidade de documentos e cotações passíveis de conciliação. O TCC considera essa condição na interpretação.
- **Onde.** TCC, "Delimitação da amostra" e "Extensão histórica". Código: `status` de cada empresa-ano em `capitalizacao.csv` e `decisoes_amostra.csv`.

### A12. Winsorização de ROE e alavancagem nos percentis 1 e 99

- **Decisão.** Valores de ROE e alavancagem além dos percentis 1 e 99 são trazidos até esses limites, sem apagar a linha. Porte e capitalização não são winsorizados. Nas retiradas de empresas, os limites do painel principal ficam fixos.
- **Por quê.** Reduz a influência de índices extremos, comuns quando o denominador é pequeno, sem perder observações numa amostra já pequena.
- **Alternativa.** Modelo sem winsorização: os sinais permanecem, e o ROE passa a −0,3567 (Tabela 7).
- **Onde.** TCC, "Fundamentos contábeis e defasagem" e nota da Tabela 3. Código: `config.py` (`PERCENTIS_WINSOR`); `painel.py` / `painel.R` (quantil tipo 7).

### A13. Efeitos fixos de empresa e de ano

- **Decisão.** Estimar a eq. 7 com α_i e λ_t por mínimos quadrados com variáveis indicadoras.
- **Por quê.** α_i absorve o que é estável em cada empresa, como o segmento de atuação. λ_t absorve o que é comum a todas as empresas num mesmo ano, como juros e condições de mercado. O coeficiente passa a medir se a empresa vale mais nos anos em que seu fundamento está acima do seu próprio padrão.
- **Consequência.** O R² global (0,9711) vem quase todo dos efeitos fixos. Por isso o TCC reporta também o R² intra-grupo (0,2130) e o parcial (0,2896).
- **Onde.** TCC, eq. 7. Código: `estimacao.py` / `estimacao.R`.

### A14. Erro-padrão CR1 com t(G−1)

- **Decisão.** Erro-padrão agrupado por empresa, com o fator G/(G−1)·(N−1)/(N−K), e distribuição t com G − 1 = 13 graus de liberdade.
- **Por quê.** Os resíduos da mesma empresa são correlacionados ao longo dos anos. Com poucos grupos, a referência t(G−1) é mais conservadora que a normal (Cameron e Miller, 2015; MacKinnon, Nielsen e Webb, 2023).
- **Alternativa.** 12 grupos societários (Elektro com Neoenergia, Taesa com Cemig): Apêndice C, Tabela 3.
- **Onde.** TCC, "Inferência e verificações de sensibilidade". Código: `estimacao.py` / `estimacao.R`.

### A15. WCR com enumeração completa como teste prioritário

- **Decisão.** O valor de p de referência é o do *wild cluster restricted bootstrap*, com as 2¹⁴ = 16.384 combinações de sinais enumeradas, sem sorteio.
- **Por quê.** Com poucos grupos, testes baseados só no CR1 tendem a rejeitar a hipótese nula com frequência maior que a nominal (MacKinnon, Nielsen e Webb, 2023). O WCR impõe a hipótese nula e mantém a dependência dentro da empresa (Cameron, Gelbach e Miller, 2008; Roodman et al., 2019). Com 14 grupos, enumerar tudo é viável, e o p fica exatamente reprodutível.
- **Limites, como no TCC.** A enumeração elimina a variação entre sorteios, mas não garante validade numa amostra pequena. O método pressupõe independência entre grupos e não ajusta resíduos pela alavancagem estatística.
- **Regra de leitura.** O CR1 dá a comparação e os intervalos. Quando os dois divergem, os dois são apresentados, sem escolher o menor p (MacKinnon, Nielsen e Webb, 2023).
- **Onde.** TCC, Inferência; Tabela 6. Código: `estimacao.py` / `estimacao.R` (`wcr`).

### A16. Holm só para as três hipóteses

- **Decisão.** O ajuste de Holm (1979) vale só para a família H1–H3 do modelo principal.
- **Por quê.** São as três hipóteses confirmatórias do trabalho. Os demais testes são diagnósticos, não novas hipóteses.
- **Resultado.** p de Holm de 0,0077 (ROE), 0,0259 (alavancagem) e 0,0122 (porte).
- **Onde.** TCC, "Critérios de interpretação e limites". Código: `estimacao.py` / `estimacao.R` (`holm`).

### A17. Driscoll–Kraay só como comparação suplementar

- **Decisão.** Driscoll–Kraay, com pesos de Bartlett e uma ou duas defasagens, aparece no Apêndice C, Tabela 4, e não no corpo do texto.
- **Por quê.** A justificativa do método supõe uma dimensão temporal longa. Com seis anos, isso não se sustenta (Driscoll e Kraay, 1998; Hoechle, 2007).
- **Onde.** TCC, Inferência; Apêndice C, Tabela 4. Código: `estimacao.py` / `estimacao.R`.

### A18. Sensibilidades como diagnósticos exploratórios

- **Decisão.** Matriz de 18 verificações (Tabela 7), especificações alternativas na mesma amostra (Tabela 8), retirada de cada empresa (Figura 1; Apêndice C, Tabela 1) e janelas de transição (Apêndice C, Tabela 2). Nenhuma recebe correção conjunta, e nenhuma substitui o modelo principal.
- **Por quê.** O objetivo é saber se a conclusão depende de uma empresa, de um ano, de um tratamento ou de uma definição de variável. O TCC diz que não houve seleção de modelo por significância e que os filtros foram aplicados antes das regressões, sem depender de coeficientes nem de valores de p.
- **Consequência.** Foi assim que apareceu a concentração da CEB: ela responde por 54,55% da variação que identifica o coeficiente do ROE, e só a observação de 2022 responde por 31,38%.
- **Onde.** TCC, Tabelas 7–8 e Apêndice C. Código: `especificacoes.py` / `especificacoes.R`.

### A19. Leitura como associação, convertida pela eq. 8

- **Decisão.** Os coeficientes são apresentados como variação percentual da capitalização: 100·[exp(β·Δx) − 1].
- **Por quê.** Com y em logaritmo, β não é variação em reais. A eq. 8 traduz para "+10 p.p. de ROE → −6,16%" e mantém a leitura como associação, não como efeito causal nem previsão para uma companhia.
- **Onde.** TCC, eq. 8. Código: `tabelas.py` / `tabelas.R` (`interpretacao_efeitos.csv`).

---

## B. Dados

Os casos concretos de cada regra estão em [decisoes.md](decisoes.md) e no relatório em PDF.

### B1. Preço e quantidade da mesma classe

- **Decisão.** Cada classe de ação entra com o próprio preço de dezembro. Se faltar o preço de uma classe, a observação sai; nunca se usa a cotação de outra classe.
- **Por quê.** ON e PN têm preços diferentes. Trocar uma pela outra muda a capitalização sem nenhum aviso.
- **Onde.** TCC, eq. 1. Código: `capitalizacao.py` / `capitalizacao.R`.

### B2. Quantidade da DFP conferida com o FRE

- **Decisão.** Antes do cálculo, a quantidade de ações da DFP é conferida com o capital informado no FRE. Isso resolve escala (unidades ou milhares), tesouraria já descontada, desdobramento aprovado depois de dezembro e tesouraria divergente.
- **Por quê.** Preço e quantidade vêm de fontes diferentes. Cada um desses problemas multiplica ou divide a capitalização sem que o dado pareça errado.
- **Onde.** TCC, Dados e Apêndice B. Código: `capitalizacao.py` / `capitalizacao.R`. Casos: [decisoes.md, seção 1](decisoes.md#1-quantidade-de-ações).

### B3. Documentos originais só quando a CVM não concilia

- **Decisão.** Cemig 2020 (nota 26), CPFL (6-K na SEC) e EDP 2010–2011 usam a quantidade dos documentos originais. Os valores não são estendidos a outros anos.
- **Por quê.** Sem o documento, essas observações sairiam. Estender o valor a outros anos seria extrapolação (A11).
- **Onde.** TCC, Dados. Código: `config.py` (`CEMIG_2020`, `EDP_2010_2011`); `dados/documentos/capital_cpfl_documentado.csv`.

### B4. Conciliação do lucro da controladora

- **Decisão.** Quando lucro total ≠ controladora + não controladores, com diferença acima de R$ 1 mil, consulta-se a DRE individual. Se ela for igual ao total consolidado e não houver não controladores, esse valor é usado. Caso contrário, o lucro fica ausente.
- **Por quê.** Na Light 2021–2024 e na Serena 2021, as parcelas vinham zeradas na base da CVM, embora o total estivesse correto.
- **Onde.** TCC, Dados. Código: `contabil.py` / `contabil.R` (`conciliar_lucro`); `config.py` (`TOLERANCIA_LUCRO`).

### B5. Listagem de 23 emissoras, sem pretensão de censo

- **Decisão.** A amostra parte de uma listagem de trabalho de 23 emissoras, identificadas por código CVM e CNPJ.
- **Limite, como no TCC.** A listagem não é um censo das elétricas da B3. Não foi localizada a documentação da consulta que a originou, nem dos motivos da ausência de Energisa, Alupar e ISA CTEEP. O pacote prova que os números decorrem dos dados e das regras declaradas, mas não que a listagem foi fixada antes da análise.
- **Onde.** TCC, Delimitação da amostra; Apêndice A. Código: `dados/cvm/universo_identificado.csv`. A conferência verifica que as 14 empresas do painel e as 9 de fora são exatamente as do Apêndice A.

---

## C. Engenharia do pacote

### C1. Fórmulas próprias, conferidas com bibliotecas

- **Decisão.** A estimação e as covariâncias (CR1, WCR, Driscoll–Kraay) são escritas com álgebra de matrizes: NumPy no Python e R base no R. As bibliotecas entram como verificação.
- **Por quê.** Cada número pode ser rastreado até uma fórmula da metodologia. O TCC declara statsmodels para os mínimos quadrados com indicadoras e linearmodels para a conferência por efeitos fixos, e o bootstrap foi implementado por enumeração em NumPy.
- **Verificação.** A conferência B compara com statsmodels e linearmodels (Python) e com fixest (R), com diferenças de no máximo 10⁻¹⁰.
- **Onde.** `estimacao.py` / `estimacao.R`; `conferencia.py` / `conferencia.R`.

### C2. Duas implementações independentes: Python e R

- **Decisão.** A análise inteira existe em Python e em R, com os mesmos módulos, partindo dos mesmos dados.
- **Por quê.** O TCC foi feito em Python, e R é amplamente usado em econometria. Duas implementações independentes que chegam aos mesmos números mostram que o resultado não depende de um detalhe de software.
- **Verificação.** `scripts/comparar_versoes.py` compara as saídas arquivo a arquivo: 30 arquivos, idênticos.

### C3. Extratos congelados, sem acesso à internet

- **Decisão.** O repositório traz os extratos usados no TCC, com o SHA-256 dos arquivos brutos. Nenhuma etapa acessa a internet.
- **Por quê.** As bases da CVM recebem reapresentações. Baixar de novo produziria outra base (A8). Congelar os extratos garante que qualquer pessoa reproduza exatamente o TCC.
- **Limite.** A seleção do último negócio de dezembro nos arquivos da B3 e a extração das contas foram feitas na coleta. Os dados de origem continuam sujeitos às condições de uso da CVM e da B3.
- **Onde.** `dados/`, `dados/fontes.json`, `dados/b3/manifesto_precos.json`, `coleta/`.

### C4. Conferência com o texto impresso do TCC

- **Decisão.** Os 498 valores impressos no TCC foram transcritos para `dados/documentos/valores_publicados_tcc.csv`, cada um com uma chave. A cada execução, o código recalcula e formata cada valor com as mesmas regras do texto e compara os textos.
- **Por quê.** Comparar o texto formatado, como "−0,6354", "< 0,0001" ou "0,0026*", prova o que foi publicado, inclusive arredondamento e asterisco. Comparar números próximos provaria menos.
- **Verificação extra.** A conferência também testa listas e códigos: as empresas dentro e fora do painel e a existência de cada rubrica do Apêndice B nos extratos da CVM.
- **Onde.** `valores.py` / `valores.R`; `conferencia.py` / `conferencia.R`; [conferencia.md](conferencia.md).

### C5. Parâmetros num único arquivo

- **Decisão.** Anos, percentis, mínimo de exercícios, tolerâncias, janelas de transição e quantidades documentadas ficam em `config.py` / `config.R`, cada um com a seção do TCC de onde vem.
- **Por quê.** Uma mudança de regra se faz num lugar só e vale para todo o estudo. A conferência C confirma que os parâmetros citados no TCC (percentis 1 e 99, mínimo de quatro anos) são os usados.

### C6. Um roteiro de relatório para as duas linguagens

- **Decisão.** O texto do relatório em PDF fica em `relatorio/roteiro.txt`, com marcadores `{chave;decimais;tipo}` para os números.
- **Por quê.** As duas versões geram o mesmo relatório sem duplicar o texto, e nenhum número do relatório é digitado: todos são calculados na hora.

### C7. Resultados idênticos entre execuções

- **Decisão.** Não há sorteio (o WCR é enumerado), e a versão Python fixa uma thread de álgebra linear (`OPENBLAS_NUM_THREADS=1`).
- **Por quê.** Os valores de p do WCR são contagens exatas. Qualquer variação entre máquinas apareceria como divergência na conferência A.

### C8. Integração contínua a cada envio

- **Decisão.** `.github/workflows/reproducao.yml` roda as duas versões, as três conferências e a comparação Python × R e a conferência de `docs/tabelas/` a cada envio ao GitHub. O selo do README mostra o resultado.
- **Por quê.** Prova, num computador limpo, que o repositório reproduz o TCC, e impede que uma alteração futura quebre a reprodução sem ninguém perceber.

### C9. Um único ramo, com pastas `python/` e `R/`

- **Decisão.** As duas versões ficam no ramo `main`, lado a lado.
- **Por quê.** Dados, documentação e roteiro são compartilhados, e a comparação Python × R precisa das duas versões juntas. Ramos separados duplicariam esse material e esconderiam uma das versões de quem abre o repositório.

### C10. Comentários linha a linha, com referências

- **Decisão.** Cada linha de código tem um comentário. Cada módulo cita, no cabeçalho, as referências da etapa que implementa.
- **Por quê.** O repositório também serve para ensinar: quem conhece o TCC deve conseguir ler o código sem conhecer a linguagem a fundo.

### C11. Licenças separadas para código e texto

- **Decisão.** Código sob MIT; textos, relatório e figuras sob CC BY 4.0.
- **Por quê.** MIT é a licença usual para código e permite reuso amplo. CC BY 4.0 é a usual para texto acadêmico e exige citação. Os dados de origem não são relicenciados: seguem os termos da CVM e da B3.

### C12. Cópia das tabelas geradas em `docs/tabelas/`

- **Decisão.** As tabelas do TCC geradas pelo código são versionadas em `docs/tabelas/`, com um índice que liga cada arquivo à tabela do trabalho.
- **Por quê.** `resultados/` não é versionada, porque é saída da execução. Sem a cópia, quem abre o repositório no GitHub não vê nenhuma tabela sem rodar o código.
- **Risco e controle.** Uma cópia pode ficar desatualizada. A integração contínua roda `scripts/conferir_tabelas_publicadas.py`, que falha se a cópia divergir do que o código gera agora.
