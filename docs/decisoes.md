# Decisões documentadas

Todos os casos abaixo são aplicados pelo código e ficam registrados nas saídas: `capitalizacao.csv` (colunas `status`, `escala` e `nota`), `correcoes_lucro.csv` e `decisoes_amostra.csv`. Regra geral do TCC: **divergência não resolvida exclui a observação; nada é estimado, preenchido ou extrapolado para anos sem comprovação.**

## 1. Quantidade de ações

| Caso | O que aconteceu | Decisão | Registro |
|---|---|---|---|
| Rio Paranapanema, 2020–2022 | A DFP informou as ações em milhares; a partir de 2023, em unidades | Multiplicou por mil nesses anos | `escala = 1000` |
| Cemig, Celesc, Elektro, Eneva, Taesa, Auren | Quantidades em milhares em todos os anos do painel | Mesma regra de escala | `escala = 1000` |
| Neoenergia, 2021–2023 | A DFP já vinha sem as ações em tesouraria | Quantidade emitida recuperada no FRE, para não descontar a tesouraria duas vezes | `DFP_liquido_reconciliado_FRE` |
| Cemig, 2020 | Quantidades conferidas na nota 26 das demonstrações (6-K na SEC) | ON 507.670.289; PN 1.011.082.312; tesouraria 71 ON e 583.709 PN | `nota26_2020` |
| CPFL, 2012 e 2014–2019 | Capital não conciliado na base da CVM | Quantidades transcritas das DFs originais (6-K na SEC); só ON, sem tesouraria | URL do documento |
| EDP, 2010–2011 | Capital ausente na base | DF de 2011, nota 26, p. 26: 158.805.204 ON e 280.225 em tesouraria (só na extensão histórica) | `DF2011_nota26_p26` |
| Copel, 2020 | Desdobramento aprovado em março de 2021 já aparecia na DFP de 2020 | Evento desfeito para casar com o preço de dezembro de 2020 (a Copel ficou fora por outro motivo) | `desfeito_evento_2021-03-11` |
| Engie e Eneva, anos antigos | Cotações com o código anterior | Tractebel (TBLE) até 2015; MPX (MPXE) até 2012 | raiz do ticker |

## 2. Lucro da controladora (Light)

Na DFP consolidada da Light, as parcelas da controladora e dos não controladores vinham zeradas, embora o lucro total não fosse zero. A DRE individual confirmou que o lucro da controladora era igual ao total consolidado.

| Exercício | Antes | Valor usado |
|---|---:|---:|
| 2021 | 0 | R$ 0,40 bilhão |
| 2022 | 0 | −R$ 5,67 bilhões |
| 2023 | 0 | R$ 0,26 bilhão |
| 2024 | 0 | R$ 1,64 bilhão |
| 2025 | não conciliado | ausente (afetaria só o mercado de 2026, fora do painel) |

A mesma correção vale para a Serena em 2021; a Serena ficou fora do painel por falta de capital e cotações.

## 3. Por que cinco empresas têm menos de seis anos

| Empresa | Anos no painel | Ano(s) de mercado ausente(s) e motivo |
|---|---|---|
| Auren | 2022–2025 | 2020–2021: empresa formada na reorganização da CESP em 2022; sem capital ou cotação conciliáveis antes |
| Elektro | 2020–2022, 2025 | 2023 e 2024: sem cotação de dezembro de uma das classes |
| Rio Paranapanema | 2020–2023 | 2024 e 2025: PL de 2023 e 2024 registrado como zero no extrato da CVM; ROE não calculável |
| Equatorial | 2021–2025 | 2020: tesouraria do FRE divergente da DFP |
| Light | 2020–2022, 2024–2025 | 2023: EBITDA de 2022 negativo (−R$ 1,18 bilhão); alavancagem não calculável |

São as 8 lacunas do painel não balanceado (9 das 14 empresas têm os seis anos).

## 4. Empresas fora do painel principal (Apêndice A, Tabela 2)

O código gera esta tabela em `tabelas_tcc/apA_tabela_2_fora_do_painel.csv`, com as contagens de anos elegíveis e os motivos de exclusão registrados, e confere que a lista é a mesma do TCC.

| Emissora | Restrição |
|---|---|
| AESO3 | Cotação por classe não conciliada |
| CEEB3 | Cotação preferencial ausente |
| CEED3 | Classes e menos de quatro anos completos |
| COCE3 | Classes, tesouraria ou cotação não conciliadas |
| CPLE3 (Copel) | Subclasses conciliadas em apenas dois exercícios, abaixo do mínimo de quatro |
| ELET3 (Eletrobras) | Subclasses conciliadas em apenas dois exercícios, abaixo do mínimo de quatro |
| EMAE3 | Cotação insuficiente |
| ENBR3 (EDP) | Tesouraria divergente e cotação insuficiente (oito observações só na extensão histórica) |
| SRNA3 (Serena) | Capital e cotações insuficientes |

As restrições referem-se aos registros disponíveis e ao mínimo de quatro anos; não demonstram inexistência de informações em outras fontes.

## 5. Detalhes das sensibilidades

- **Negócios desde 20 de dezembro (73 observações).** Saem Celesc 2024 (último negócio em 18/12), Elektro 2021 (14/12) e Rio Paranapanema 2021 (1º/12). Com mais de uma classe, vale a data mais antiga entre elas.
- **Sem transições (69, e não 68).** Saem CEB 2021–2022, Auren 2022–2025 e Light 2024; a Light de 2023 já estava fora. A exclusão conjunta não reaplica o mínimo de quatro anos.
- **Contemporâneo (73).** Saem Rio Paranapanema 2023 (PL zero), Light 2022 (EBITDA negativo no próprio ano) e Light 2025 (lucro não conciliado).
- **ROE médio (74) e PL médio (75).** As linhas perdidas são da Auren: 2022 nos dois testes e 2023 no ROE médio. A regra de escopo constante não retirou nenhuma linha.
- **Dívida ampliada.** A alavancagem média sem winsorização cai de 2,5057 para 2,2793 vezes; a conta 1.01.02 existe nas 76 observações.
- **Mesmo p em dois testes.** Sem a CEB e sem a Light, o p WCR da alavancagem é 0,0598 nos dois casos: 490 de 8.192 combinações. Não é erro de cópia.
