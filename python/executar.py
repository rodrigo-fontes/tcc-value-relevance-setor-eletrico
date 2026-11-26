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
    3  tabelas               todas as tabelas do TCC e Figura 1               (tcc.tabelas)
    4  conferir              pacote original, bibliotecas e texto do TCC      (tcc.conferencia)
    5  relatório             PDF explicado, com a conferência item a item     (tcc.relatorio)

Tudo é gravado em resultados/python/. Nenhuma etapa acessa a internet.
"""
import argparse                                             # argumentos de linha de comando
import json                                                 # funil.json
import os                                                   # variáveis de ambiente
import sys                                                  # caminho do pacote e código de saída
import time                                                 # tempo de execução
from pathlib import Path                                      # caminhos

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")          # resultados idênticos entre máquinas (uma thread)
sys.path.insert(0, str(Path(__file__).resolve().parent))   # pasta python/: torna o pacote tcc importável

from tcc import config as C                                 # noqa: E402  (importa depois de ajustar o caminho)


def etapa_1():                                                # etapa 1
    """Base empresa-ano: capitalização (eq. 1), fundamentos (eqs. 3–6) e painéis."""
    from tcc import entradas, capitalizacao, contabil, painel  # módulos da construção da base
    d = entradas.carregar()                                 # extratos congelados
    cap, comp = capitalizacao.calcular(d)                   # VM por classe, conciliada
    fin, correcoes = contabil.montar(d)                     # ROE, EBITDA, AL, PORTE por exercício
    dec = painel.decisoes(cap, fin)                         # t com fundamentos de t−1
    for rotulo in ("principal", "historico"):                 # dois painéis
        z = painel.montar(dec, rotulo)                      # filtros e winsorização
        z.to_csv(C.RESULTADOS / f"painel_{rotulo}.csv", index=False)  # grava o painel
        dentro = set(zip(z.ticker, z.ano))                  # pares (empresa, ano) incluídos
        dec["incluido_" + rotulo] = [(t, a) in dentro for t, a in zip(dec.ticker, dec.ano)]  # marca as empresas-ano incluídas
        print(f"  painel {rotulo}: {len(z)} observações, {z.ticker.nunique()} empresas")  # acompanhamento
    fun = painel.funil(dec)                                 # 138 → 90 → 84 → 76
    (C.RESULTADOS / "funil.json").write_text(json.dumps(fun, indent=2))  # grava funil.json
    print("  funil:", fun)                                    # acompanhamento
    cap.to_csv(C.RESULTADOS / "capitalizacao.csv", index=False)  # grava capitalizacao.csv
    comp.to_csv(C.RESULTADOS / "componentes_capitalizacao.csv", index=False)  # grava os componentes por classe
    fin.to_csv(C.RESULTADOS / "financeiro.csv", index=False)  # grava financeiro.csv
    correcoes.to_csv(C.RESULTADOS / "correcoes_lucro.csv", index=False)  # grava correcoes_lucro.csv
    dec.to_csv(C.RESULTADOS / "decisoes_amostra.csv", index=False)  # grava decisoes_amostra.csv


def etapa_2():                                                # etapa 2
    """Catálogo de modelos com CR1, WCR e Driscoll–Kraay; Holm; VIF; concentração."""
    import pandas as pd                                       # leitura dos painéis
    from tcc import especificacoes                            # catálogo de modelos
    s = C.RESULTADOS                                          # pasta de resultados
    especificacoes.estimar_todos(pd.read_csv(s / "painel_principal.csv"), pd.read_csv(s / "painel_historico.csv"),  # painéis principal e histórico ...
                                 pd.read_csv(s / "financeiro.csv"), pd.read_csv(s / "componentes_capitalizacao.csv"), s)  # ... contas, componentes e destino


def etapa_3():                                                # etapa 3
    """Tabelas no formato do TCC e Figura 1."""
    from tcc import tabelas                                   # tabelas do TCC
    t7, cont = tabelas.gerar(C.RESULTADOS)                    # gera tabelas e Figura 1
    print("  Tabela 7: linhas significativas (rentabilidade, alavancagem, porte):", cont)  # contagens 12/13/15


def etapa_4():                                                # etapa 4
    """Três conferências; devolve False se alguma falhar."""
    from tcc import conferencia                               # conferências A, B e C
    return conferencia.executar(C.RESULTADOS)                 # True se tudo coincidir


def etapa_5():                                                # etapa 5
    """Relatório em PDF."""
    from tcc import relatorio                                 # relatório em PDF
    relatorio.gerar()                                         # gera o PDF


ETAPAS = [("Construir a base", etapa_1), ("Estimar os modelos", etapa_2), ("Tabelas do TCC", etapa_3),  # nome e função de cada etapa
          ("Conferir", etapa_4), ("Relatório em PDF", etapa_5)]  # (continuação)

if __name__ == "__main__":                                    # só quando executado diretamente
    p = argparse.ArgumentParser(description="Reprodução do TCC em Python")  # argumentos de linha de comando
    p.add_argument("--ate", type=int, default=5, help="última etapa a executar (1 a 5)")  # --ate N: para depois da etapa N
    args = p.parse_args()                                     # lê os argumentos
    C.RESULTADOS.mkdir(parents=True, exist_ok=True)         # cria resultados/python/
    conferido = True                                          # muda para False se a conferência falhar
    for i, (nome, f) in enumerate(ETAPAS[: args.ate], start=1):  # etapas 1 a N
        t0 = time.time()                                      # início da etapa
        print(f"\n===== Etapa {i}: {nome} =====", flush=True)  # título
        r = f()                                               # executa
        conferido = conferido and r is not False            # só a etapa 4 devolve um booleano
        print(f"  ({time.time() - t0:.1f} s)")                # tempo da etapa
    if args.ate >= 5:                                         # se o relatório foi gerado
        print(f"\nRelatório: {C.RESULTADOS / 'relatorio_reproducao.pdf'}")  # mostra onde está
    sys.exit(0 if conferido else 1)                         # código 1 se a conferência acusou diferença
