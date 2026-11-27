"""
conferir_tabelas_publicadas.py — Confere as tabelas publicadas em docs/tabelas/
==============================================================================

Uso (na raiz do repositório, depois de rodar a versão Python):

    python python/executar.py
    python scripts/conferir_tabelas_publicadas.py              # confere
    python scripts/conferir_tabelas_publicadas.py --atualizar  # copia de novo

docs/tabelas/ guarda uma cópia das tabelas do TCC geradas pelo código, para que
possam ser lidas no GitHub sem rodar nada. Este script garante que a cópia é
igual ao que o código gera agora (célula a célula) e encerra com código 1 se
alguma tabela estiver desatualizada, faltar ou sobrar.
"""
import shutil                                                # cópia de arquivos
import sys                                                   # argumentos e código de saída
from pathlib import Path                                     # caminhos
import pandas as pd                                          # leitura dos CSVs

RAIZ = Path(__file__).resolve().parents[1]                   # raiz do repositório
GERADAS = RAIZ / "resultados" / "python" / "tabelas_tcc"     # tabelas que o código acabou de gerar
PUBLICADAS = RAIZ / "docs" / "tabelas"                       # cópia versionada, lida no GitHub

geradas = {a.name for a in GERADAS.glob("*.csv")}            # nomes das tabelas geradas
if not geradas:                                              # o código ainda não foi executado
    sys.exit("Rode antes: python python/executar.py")        # mensagem e código 1

if "--atualizar" in sys.argv:                                # modo de atualização
    for a in PUBLICADAS.glob("*.csv"):                       # apaga as cópias antigas
        a.unlink()                                           # (uma tabela removida do código some daqui)
    for n in sorted(geradas):                                # copia cada tabela gerada
        shutil.copyfile(GERADAS / n, PUBLICADAS / n)         # cópia byte a byte
    print(f"{len(geradas)} tabelas copiadas para docs/tabelas/.")  # resumo
    sys.exit(0)                                              # termina sem conferir

publicadas = {a.name for a in PUBLICADAS.glob("*.csv")}      # nomes das cópias versionadas
falhas = sorted(geradas ^ publicadas)                        # tabelas que faltam ou sobram
for n in sorted(geradas & publicadas):                       # cada tabela presente nos dois lados
    a = pd.read_csv(GERADAS / n, dtype=str, keep_default_na=False)   # gerada, como texto
    b = pd.read_csv(PUBLICADAS / n, dtype=str, keep_default_na=False)  # publicada, como texto
    ok = a.shape == b.shape and list(a.columns) == list(b.columns) and bool((a.values == b.values).all())  # célula a célula
    print(f"  [{'ok' if ok else 'DIFERENTE'}] docs/tabelas/{n}")  # linha do relatório
    if not ok:                                               # divergiu
        falhas.append(n)                                     # registra
for n in sorted(geradas ^ publicadas):                       # nomes de um lado só
    print(f"  [{'FALTA' if n in geradas else 'SOBRA'}] docs/tabelas/{n}")  # linha do relatório
print("\nTABELAS PUBLICADAS ATUALIZADAS." if not falhas else  # resultado final
      f"\n{len(falhas)} tabela(s) desatualizada(s): rode com --atualizar e versione o resultado.")  # (continuação)
sys.exit(1 if falhas else 0)                                 # código de saída para a integração contínua
