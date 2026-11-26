# Referência: saídas do pacote original

Arquivos gerados pelo pacote de reprodução original (`Base_final_TCC`, setembro de 2026), que produziu os números publicados no TCC. **Não são usados como entrada**: servem apenas para a conferência A (`conferencia.py` / `conferencia.R`), que exige que as saídas deste repositório sejam idênticas a eles. Na coluna "Comparado com", `resultados/` significa `resultados/python/` ou `resultados/r/`.

| Arquivo | Conteúdo | Comparado com |
|---|---|---|
| `capitalizacao_final.csv`, `componentes_final.csv` | Capitalização e componentes por classe | `resultados/capitalizacao.csv`, `componentes_capitalizacao.csv` |
| `financeiro_final.csv`, `correcoes_lucro.csv` | Contas e fundamentos; conciliação do lucro | `resultados/financeiro.csv`, `correcoes_lucro.csv` |
| `decisoes_amostra.csv`, `painel_principal.csv`, `painel_historico.csv` | Decisões e painéis | mesmos nomes em `resultados/` |
| `estimativas_integral.csv`, `modelos_integral.csv` | CR1, WCR (contagens exatas), N, G, K e R² de 37 modelos | `resultados/coeficientes.csv`, `modelos.csv` |
| `estimativas_revisao.csv`, `estimativas_finais.csv` | Driscoll–Kraay | `resultados/coeficientes.csv` |
| `bootstrap_revisao.csv`, `bootstrap_final.csv` | p WCR dos modelos da revisão | `resultados/coeficientes.csv` |
| `modelos_finais.csv`, `modelos_revisao.csv` | R² global | `resultados/modelos.csv` |
| `holm_principal.csv`, `diagnosticos.json`, `diagnosticos_revisao.json` | Holm e VIF | `resultados/holm.csv`, `diagnosticos.json` |
| `variacao_por_empresa.csv`, `influencia_observacoes.csv` | Concentração (FWL) e influência | mesmos nomes em `resultados/` |
| Demais arquivos | Painéis intermediários, descritivas, matriz de p e manifestos da coleta original | preservados para rastreabilidade |
