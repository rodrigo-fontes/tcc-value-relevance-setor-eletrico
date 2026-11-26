# Versão Python — pacote `tcc`

Implementação em Python do pacote de reprodução. A estatística é escrita com álgebra de matrizes em NumPy, para que cada número possa ser rastreado até uma fórmula. A estimação é a mesma descrita no TCC (mínimos quadrados com indicadores de empresa e de ano, via statsmodels): o pacote calcula em NumPy e a conferência B refaz tudo com statsmodels e linearmodels, com diferença máxima de 10⁻¹⁰.

## Instalação e execução

Na raiz do repositório:

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r python/requirements.txt
python python/executar.py              # as cinco etapas (~12 s)
python python/executar.py --ate 3      # só construção, estimação e tabelas
```

As saídas vão para `resultados/python/`. O código de saída é 1 se a conferência acusar diferença; é assim que a integração contínua verifica cada envio.

## Módulos (na ordem do pipeline)

| Módulo | Etapa do TCC | Funções principais |
|---|---|---|
| `executar.py` | executa as cinco etapas (`--ate N` para parar antes) | `etapa_1` … `etapa_5` |
| `tcc/config.py` | parâmetros do estudo (anos, mínimos, percentis, tolerâncias, janelas, grupos) | — |
| `tcc/entradas.py` | fontes de dados | `carregar`, `lucro_individual`, `aplicacoes_financeiras` |
| `tcc/capitalizacao.py` | eq. (1) e conciliação acionária | `calcular`, `quantidades_dfp`, `quantidades_fre`, `quantidades_por_classe`, `aplicar_cpfl` |
| `tcc/contabil.py` | eqs. (3)–(6) e conciliação do lucro | `montar`, `conciliar_lucro` |
| `tcc/painel.py` | eq. (2), defasagem, filtros, winsorização, funil | `decisoes`, `montar`, `winsorizar`, `funil` |
| `tcc/estimacao.py` | eq. (7), CR1, WCR, Driscoll–Kraay, Holm, R², VIF, FWL | `estimar`, `wild_cluster_restrito`, `driscoll_kraay`, `holm`, `vif_intra`, `fracao_fwl` |
| `tcc/especificacoes.py` | Tabelas 7 e 8; Apêndice C | `painel_completo`, `painel_contemporaneo`, `catalogo`, `estimar_todos` |
| `tcc/tabelas.py` | Tabelas 1–8, Apêndices A, B e C, Figura 1; eq. (8) | `gerar`, `tabelas_descritivas`, `elegibilidade`, `desenhar_figura1` |
| `tcc/valores.py` | números citados no TCC | `valor`, `formatar` |
| `tcc/conferencia.py` | Apêndice B (reprodução) | `pacote_original`, `bibliotecas`, `texto_do_tcc`, `executar` |
| `tcc/relatorio.py` | relatório em PDF | `gerar` |

## Usando as funções diretamente

```python
import sys; sys.path.insert(0, "python")                     # na raiz do repositório
import pandas as pd
from tcc.estimacao import estimar

painel = pd.read_csv("resultados/python/painel_principal.csv")   # gerado pela etapa 1
modelo, coefs, _ = estimar(painel, "principal")              # eq. (7) com CR1, WCR e Driscoll–Kraay
print(pd.DataFrame(coefs)[["variavel", "coef", "se_CR1", "p_CR1", "p_WCR", "excedencias"]])
```

Para estimar sem uma empresa: `estimar(painel[painel.ticker != "CEBR3"], "sem_CEB")`. Para usar os 12 grupos societários na inferência, crie a coluna `grupo` e passe `grupo="grupo"`.
