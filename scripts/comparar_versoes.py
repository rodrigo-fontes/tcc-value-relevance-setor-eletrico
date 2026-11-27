"""
comparar_versoes.py — Confere se as versões Python e R produzem os mesmos resultados
====================================================================================

Uso (na raiz do repositório, depois de rodar as duas versões):

    python python/executar.py
    Rscript R/executar.R
    python scripts/comparar_versoes.py

Compara, arquivo a arquivo, resultados/python/ com resultados/r/:
    • arquivos de dados (14): colunas numéricas com diferença relativa ≤ 10⁻⁹ e texto idêntico;
    • tabelas do TCC (15) e interpretação da eq. 8: conteúdo idêntico, célula a célula.
Encerra com código 1 se algo divergir.
"""
import sys                                                   # código de saída
from pathlib import Path                                     # caminhos
import numpy as np                                           # comparação numérica
import pandas as pd                                          # leitura dos CSVs

RAIZ = Path(__file__).resolve().parents[1]                   # raiz do repositório
PY, RR = RAIZ / "resultados" / "python", RAIZ / "resultados" / "r"   # saídas das duas versões
falhas = []                                                  # arquivos que divergiram


def texto(s: pd.Series) -> pd.Series:                         # normaliza texto para comparar
    """Texto normalizado: ausente = vazio; '2020.0' = '2020' (R e pandas escrevem inteiros de formas diferentes)."""
    return s.fillna("").astype(str).str.replace(r"\.0$", "", regex=True)  # ausente = vazio; "2020.0" = "2020"


for arq in sorted(PY.glob("*.csv")):                         # arquivos de dados
    a, b = pd.read_csv(arq), pd.read_csv(RR / arq.name)      # Python e R
    ok = len(a) == len(b) and set(a.columns) == set(b.columns)   # mesmas linhas e colunas
    for c in (a.columns if ok else []):                      # coluna a coluna
        if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):  # coluna numérica nas duas versões?
            ok &= bool(np.allclose(a[c].astype(float), b[c].astype(float), rtol=1e-9, atol=1e-12, equal_nan=True))  # iguais até 10⁻⁹ (relativo)
        else:                                                 # coluna de texto
            ok &= texto(a[c]).equals(texto(b[c]))            # texto idêntico
    print(f"  [{'ok' if ok else 'DIFERENTE'}] {arq.name}")    # linha do relatório
    if not ok:                                                # divergiu
        falhas.append(arq.name)                               # registra

for arq in sorted((PY / "tabelas_tcc").glob("*.csv")):       # tabelas do TCC
    a, b = pd.read_csv(arq), pd.read_csv(RR / "tabelas_tcc" / arq.name)  # Python e R
    ok = a.shape == b.shape and a.astype(str).equals(b.astype(str))   # célula a célula
    print(f"  [{'ok' if ok else 'DIFERENTE'}] tabelas_tcc/{arq.name}")  # linha do relatório
    if not ok:                                                # divergiu
        falhas.append(arq.name)                               # registra

print("\n" + ("PYTHON E R IDÊNTICOS." if not falhas else f"{len(falhas)} ARQUIVO(S) DIFERENTE(S): {falhas}"))  # resultado final
sys.exit(1 if falhas else 0)                                  # código 1 se algo divergiu
