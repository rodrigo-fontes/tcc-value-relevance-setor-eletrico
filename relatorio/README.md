# Roteiro do relatório em PDF

`roteiro.txt` contém o texto do relatório de reprodução e é lido pelas duas implementações (`python/tcc/relatorio.py` e `R/relatorio.R`), que geram PDFs equivalentes.

| Sintaxe | Efeito |
|---|---|
| `% texto` | Comentário (ignorado) |
| `## Título` / `### Título` | Seção (página nova) / subseção |
| texto | Parágrafo (linhas seguidas são unidas; linha em branco separa) |
| `- item` | Lista com marcadores |
| `> texto` | Quadro de destaque |
| `\| a \| b \|` | Tabela fixa (a primeira linha é o cabeçalho) |
| `@formula texto` | Fórmula centralizada |
| `@tabela arquivo.csv \| título \| nota \| cab1;cab2;…` | Tabela de `resultados/<linguagem>/tabelas_tcc/` |
| `@capa`, `@funil`, `@decisoes_capital`, `@correcoes_lucro`, `@lacunas`, `@figura1`, `@conferencia_resumo`, `@conferencia_detalhe` | Blocos montados pelo código |
| `@nomes chave=rótulo;…` | Rótulos das variáveis nas tabelas |
| `{chave;decimais;tipo}` | Número calculado na hora, com a mesma regra da conferência (ex.: `{coef\|principal\|roe_lag;4;num}` → −0,6354) |

Os números do texto nunca são digitados: se um resultado mudar, o relatório muda junto.
