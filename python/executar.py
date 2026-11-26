"""
executar.py — Roda a reprodução completa do TCC em Python
=========================================================

Uso (na raiz do repositório):

    pip install -r python/requirements.txt
    python python/executar.py                 # todas as etapas
    python python/executar.py --ate 3         # só até a etapa 3 (sem conferência e relatório)

Etapas:
    1  construir a base      capitalização, contas, fundamentos, painéis       (tcc.capitalizacao, contabil, painel)
    2  estimar               modelo principal e 43 especificações             (tcc.especificacoes, estimacao)
    3  tabelas               Tabelas 1, 4–8, Apêndice C e Figura 1            (tcc.tabelas)
    4  conferir              pacote original, bibliotecas e texto do TCC      (tcc.conferencia)
    5  relatório             PDF explicado, com a conferência item a item     (tcc.relatorio)

Tudo é gravado em resultados/python/. Nenhuma etapa acessa a internet.
"""
import argparse                                             # argumentos de linha de comando
import json                                                 # funil.json
import os                                                   # variáveis de ambiente
import sys                                                  # caminho do pacote e código de saída
import time                                                 # tempo de execução
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")          # resultados idênticos entre máquinas (uma thread)
sys.path.insert(0, str(Path(__file__).resolve().parent))   # pasta python/: torna o pacote tcc importável

from tcc import config as C                                 # noqa: E402  (importa depois de ajustar o caminho)


def etapa_1():
    """Base empresa-ano: capitalização (eq. 1), fundamentos (eqs. 3–6) e painéis."""
    from tcc import entradas, capitalizacao, contabil, painel
    d = entradas.carregar()                                 # extratos congelados
    cap, comp = capitalizacao.calcular(d)                   # VM por classe, conciliada
    fin, correcoes = contabil.montar(d)                     # ROE, EBITDA, AL, PORTE por exercício
    dec = painel.decisoes(cap, fin)                         # t com fundamentos de t−1
    for rotulo in ("principal", "historico"):
        z = painel.montar(dec, rotulo)                      # filtros e winsorização
        z.to_csv(C.RESULTADOS / f"painel_{rotulo}.csv", index=False)
        dentro = set(zip(z.ticker, z.ano))                  # pares (empresa, ano) incluídos
        dec["incluido_" + rotulo] = [(t, a) in dentro for t, a in zip(dec.ticker, dec.ano)]
        print(f"  painel {rotulo}: {len(z)} observações, {z.ticker.nunique()} empresas")
    fun = painel.funil(dec)                                 # 138 → 90 → 84 → 76
    (C.RESULTADOS / "funil.json").write_text(json.dumps(fun, indent=2))
    print("  funil:", fun)
    cap.to_csv(C.RESULTADOS / "capitalizacao.csv", index=False)
    comp.to_csv(C.RESULTADOS / "componentes_capitalizacao.csv", index=False)
    fin.to_csv(C.RESULTADOS / "financeiro.csv", index=False)
    correcoes.to_csv(C.RESULTADOS / "correcoes_lucro.csv", index=False)
    dec.to_csv(C.RESULTADOS / "decisoes_amostra.csv", index=False)


def etapa_2():
    """Catálogo de modelos com CR1, WCR e Driscoll–Kraay; Holm; VIF; concentração."""
    import pandas as pd
    from tcc import especificacoes
    s = C.RESULTADOS
    especificacoes.estimar_todos(pd.read_csv(s / "painel_principal.csv"), pd.read_csv(s / "painel_historico.csv"),
                                 pd.read_csv(s / "financeiro.csv"), pd.read_csv(s / "componentes_capitalizacao.csv"), s)


def etapa_3():
    """Tabelas no formato do TCC e Figura 1."""
    from tcc import tabelas
    t7, cont = tabelas.gerar(C.RESULTADOS)
    print("  Tabela 7: linhas significativas (rentabilidade, alavancagem, porte):", cont)


def etapa_4():
    """Três conferências; devolve False se alguma falhar."""
    from tcc import conferencia
    return conferencia.executar(C.RESULTADOS)


def etapa_5():
    """Relatório em PDF."""
    from tcc import relatorio
    relatorio.gerar()


ETAPAS = [("Construir a base", etapa_1), ("Estimar os modelos", etapa_2), ("Tabelas do TCC", etapa_3),
          ("Conferir", etapa_4), ("Relatório em PDF", etapa_5)]

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Reprodução do TCC em Python")
    p.add_argument("--ate", type=int, default=5, help="última etapa a executar (1 a 5)")
    args = p.parse_args()
    C.RESULTADOS.mkdir(parents=True, exist_ok=True)         # cria resultados/python/
    conferido = True
    for i, (nome, f) in enumerate(ETAPAS[: args.ate], start=1):
        t0 = time.time()
        print(f"\n===== Etapa {i}: {nome} =====", flush=True)
        r = f()
        conferido = conferido and r is not False            # só a etapa 4 devolve um booleano
        print(f"  ({time.time() - t0:.1f} s)")
    if args.ate >= 5:
        print(f"\nRelatório: {C.RESULTADOS / 'relatorio_reproducao.pdf'}")
    sys.exit(0 if conferido else 1)                         # código 1 se a conferência acusou diferença
