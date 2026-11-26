# Coleta (scripts originais)

Scripts usados na coleta original para baixar extratos adicionais da CVM. **Não fazem parte do pipeline**, que parte dos extratos já congelados em `dados/`, e exigem acesso à internet.

| Script | O que baixa | Saída |
|---|---|---|
| `coletar_lucro.py` | Conta 3.11 da DRE individual de 2021–2024 (Light e Serena) | `dados/cvm_complementar/lucro_individual_*.csv` e `catalogo_lucro.json` |
| `coletar_complementos.py` | BPA, BPP, DRE e DFC de 2019–2024 das 23 emissoras | `dados/cvm_complementar/complementos_*.csv` e `catalogo_complementos.json` |

Os pacotes da CVM podem ser reapresentados depois da coleta. Uma nova extração deve ser tratada como outra versão dos dados, e não como substituta dos extratos preservados.
