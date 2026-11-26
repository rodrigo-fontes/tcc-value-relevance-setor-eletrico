"""
tcc.relatorio — Relatório de reprodução em PDF
==============================================

Monta `resultados/python/relatorio_reproducao.pdf` (cerca de 27 páginas) a partir de:
    relatorio/roteiro.txt                          texto e ordem das seções (o mesmo arquivo da versão R)
    resultados/                                    saídas das etapas 1 a 3
    dados/documentos/valores_publicados_tcc.csv    números impressos no TCC (seção 6 e anexo)

O texto não traz números digitados: o roteiro usa marcadores {chave;decimais;tipo},
preenchidos por `tcc.valores` — a mesma regra da conferência. Se um resultado mudar,
o texto muda junto.

Diagramação: página A4 (8,27 × 11,69 polegadas), medidas em polegadas a partir do
topo, quebra de linha gulosa por número de caracteres. A versão em R usa a mesma
geometria, para que os dois PDFs fiquem praticamente iguais.
"""
import re                                                    # marcadores e conversão de números
from datetime import date                                    # data na capa
import numpy as np                                           # somas acumuladas
import pandas as pd                                          # tabelas
import matplotlib                                            # desenho do PDF
matplotlib.use("Agg")                                        # sem janela: grava direto em arquivo
import matplotlib.pyplot as plt                              # figuras (uma por página)
from matplotlib.backends.backend_pdf import PdfPages         # PDF de várias páginas
from matplotlib.patches import Rectangle                     # faixas coloridas
from . import config as C                                    # caminhos
from .valores import valor as _valor, formatar, _res         # chave → número formatado
from .tabelas import desenhar_figura1                        # a mesma Figura 1 do PNG

LINGUAGEM = "Python"                                         # aparece na capa e no rodapé

# =============================================================================
# 1. Dados usados pelo relatório (preenchidos por _carregar)
# =============================================================================
cap = dec = fin = cor = pub = d = h = fun = coef_df = None   # tabelas de resultados
n_ok = n_tot = 0                                             # conferência com o TCC


def valor(chave):
    """Valor de uma chave na pasta de resultados."""
    return _valor(chave, C.RESULTADOS)                       # mesma função da conferência


def br(s):
    """Converte os números de uma célula de CSV para o formato brasileiro (vírgula e sinal −)."""
    s = re.sub(r"(?<![\w/.])-(?=\d)", "−", str(s))           # hífen antes de dígito → sinal de menos
    return re.sub(r"(\d)\.(\d)", r"\1,\2", s)                # ponto decimal → vírgula


def _carregar():
    """Lê os resultados e refaz a conferência com os valores publicados no TCC."""
    global cap, dec, fin, cor, pub, d, h, fun, coef_df, n_ok, n_tot
    s = C.RESULTADOS                                         # pasta resultados/
    cap = pd.read_csv(s / "capitalizacao.csv")               # decisões de capitalização
    dec = pd.read_csv(s / "decisoes_amostra.csv")            # inclusão de cada empresa-ano
    fin = pd.read_csv(s / "financeiro.csv")                  # fundamentos por exercício
    cor = pd.read_csv(s / "correcoes_lucro.csv")             # conciliação do lucro
    r = _res(s)                                              # tabelas já carregadas por tcc.valores
    d, h, fun = r["d"], r["h"], r["fun"]                     # painéis e funil
    coef_df = pd.read_csv(s / "coeficientes.csv")            # coeficientes (Figura 1)
    pub = pd.read_csv(C.DADOS / "documentos" / "valores_publicados_tcc.csv", dtype=str, keep_default_na=False)
    pub["calculado"] = [formatar(valor(c), dc, t) for c, dc, t in zip(pub.chave, pub.decimais, pub.tipo)]
    pub["confere"] = pub.calculado == pub.publicado          # mesma comparação de tcc.conferencia
    n_ok, n_tot = int(pub.confere.sum()), len(pub)           # 465 de 465


# =============================================================================
# 2. Tabelas montadas na hora: (título, cabeçalho, linhas, nota)
# =============================================================================
MOTIVO = {                                                   # status de capitalização → texto
    "excluir_capital_ambiguo_ou_ausente": "capital ausente ou ambíguo no FRE",
    "excluir_preco_classe_ausente": "sem cotação de dezembro de alguma classe",
    "excluir_subclasses_ou_tesouraria": "subclasses PNA/PNB sem repartição única documentada",
    "excluir_divergencia_tesouraria_DFP_FRE": "tesouraria do FRE diverge da DFP",
    "excluir_divergencia_tesouraria_FRE": "tesouraria do FRE ambígua",
    "excluir_tesouraria_nao_documentada": "tesouraria não documentada",
    "excluir_tesouraria_evento_posterior": "evento societário posterior com tesouraria",
    "excluir_quantidade_invalida": "quantidade de ações inválida"}


def nota_capital(n):
    """Traduz a coluna `nota` de capitalizacao.csv para texto legível."""
    if n.startswith("http"):                                 # CPFL: a nota é a URL do documento
        return "quantidade transcrita da DF original (6-K na SEC)"
    trad = {"nota26_2020": "quantidades da nota 26 das DFs (6-K na SEC)",            # Cemig 2020
            "DFP_liquido_reconciliado_FRE": "DFP já sem tesouraria: emitidas recuperadas no FRE",   # Neoenergia
            "DF2011_nota26_p26": "DF de 2011, nota 26, p. 26"}                      # EDP 2010–2011
    partes = []                                              # uma nota pode ter mais de uma decisão
    for x in n.split(";"):                                   # cada decisão
        if x.startswith("desfeito_evento_"):                 # evento societário desfeito (Copel 2020)
            partes.append("evento aprovado em " + x[16:] + " desfeito")
        else:                                                # demais decisões
            partes.append(trad.get(x, x))
    return "; ".join(partes)                                 # texto final


def t_decisoes():
    """Decisões documentadas na quantidade de ações e empresas com quantidades em milhares."""
    c = cap[cap.nota.notna() & (cap.nota != "")].merge(      # empresas-ano com alguma decisão registrada
        dec[["ticker", "ano", "incluido_principal", "incluido_historico"]], on=["ticker", "ano"])
    linhas = [[r.ticker, str(r.ano),                         # empresa e ano
               "sim" if r.incluido_principal else ("histórico" if r.incluido_historico else "não"),   # painel
               nota_capital(r.nota)] for r in c.itertuples()]                                         # decisão
    t1 = ("Decisões documentadas na quantidade de ações", ["Empresa", "Ano", "No painel", "Decisão"], linhas,
          "Fonte: capitalizacao.csv (coluna nota). 'Histórico': só na extensão 2012–2025.")
    e = cap[(cap.escala == 1000) & cap.ano.between(2020, 2025) & cap.ticker.isin(d.ticker)]   # escala em milhares
    g = e.groupby("ticker").ano.agg(lambda s: ", ".join(str(a) for a in sorted(s)))          # anos por empresa
    t2 = ("Empresas do painel com quantidades informadas em milhares (2020–2025)", ["Empresa", "Anos multiplicados por mil"],
          [[t, a] for t, a in g.items()], "A escala é a que faz a quantidade da DFP coincidir com o capital do FRE.")
    return [t1, t2]                                          # duas tabelas


def t_correcoes():
    """Conciliação do lucro da controladora (Light e Serena)."""
    sit = {"confirmado_DRE_individual_igual_consolidado": "DRE individual confirmou o total consolidado",
           "excluido_lucro_inconsistente": "não conciliado: lucro fica ausente"}
    f = lambda x: "—" if pd.isna(x) else formatar(x / 1e9, 2, "num")      # R$ bilhões, vírgula decimal
    linhas = [[r.ticker, str(r.ano), f(r.anterior), f(r.corrigido), sit[r.status]] for r in cor.itertuples()]
    return [("Conciliação do lucro da controladora (R$ bilhões)", ["Empresa", "Exercício", "Antes", "Usado", "Situação"],
             linhas, "Light 2025 afetaria só o mercado de 2026, fora do painel. A Serena ficou fora do painel por outros motivos.")]


def t_funil():
    """Funil da amostra principal: 138 → 90 → 84 → 76."""
    nomes = [("combinacoes", "Combinações possíveis (23 emissoras × 6 anos)"),
             ("capitalizacao_conciliada", "Com capitalização conciliada"),
             ("tres_fundamentos_validos", "Com os três fundamentos do ano anterior"),
             ("minimo_quatro_anos", "Com mínimo de quatro exercícios por empresa (painel principal)")]
    return [("Funil da amostra principal (2020–2025)", ["Etapa", "Empresas-ano"],
             [[n, str(fun[k])] for k, n in nomes], "Resultado: 76 observações de 14 empresas.")]


def t_lacunas():
    """Motivo de cada ano ausente das 14 empresas do painel principal (8 lacunas)."""
    linhas = []                                              # uma linha por lacuna
    for e in sorted(d.ticker.unique()):                      # empresas do painel
        for a in range(2020, 2026):                          # anos de mercado
            r = dec[(dec.ticker == e) & (dec.ano == a)].iloc[0]          # decisão da empresa-ano
            if r.incluido_principal:                         # presente no painel: não é lacuna
                continue
            if r.status != "ok":                             # falhou na capitalização
                mot = MOTIVO.get(r.status, r.status)
            else:                                            # falhou nos fundamentos de t−1
                f = fin[(fin.ticker == e) & (fin.ano == a - 1)]
                if len(f) == 0:                              # sem DFP do ano anterior
                    mot = "sem demonstração do ano anterior"
                else:
                    f = f.iloc[0]                            # exercício t−1
                    m = []                                   # motivos
                    if pd.isna(f.roe):                       # ROE ausente: lucro não conciliado ou PL ≤ 0
                        m.append("lucro da controladora não conciliado" if pd.isna(f.lucro_controladora)
                                 else f"PL de {a - 1} não positivo: ROE não calculável")
                    if pd.isna(f.dl):                        # alavancagem ausente: EBITDA ≤ 0
                        m.append(f"EBITDA de {a - 1} não positivo: alavancagem não calculável")
                    mot = "; ".join(m)                       # junta os motivos
            linhas.append([e, str(a), mot])                  # registra a lacuna
    return [("Anos ausentes das empresas do painel principal", ["Empresa", "Ano de mercado", "Motivo"], linhas,
             "Fundamentos do ano anterior ao de mercado. Nenhum valor ausente foi preenchido.")]


def t_conf_resumo():
    """Resumo da conferência com o TCC, por tabela."""
    g = pub.groupby("tabela", sort=False).confere.agg(["size", "sum"])      # valores e acertos por origem
    linhas = [[t, str(int(r["size"])), str(int(r["sum"]))] for t, r in g.iterrows()]
    linhas.append(["Total", str(n_tot), str(n_ok)])          # 465 / 465
    return [("Valores do TCC recalculados", ["Origem no TCC", "Valores", "Coincidem"], linhas,
             "Comparação do texto formatado: mesmas casas decimais, vírgula e '< 0,0001'.")]


def t_conf_detalhe():
    """Anexo: os 465 valores, um a um."""
    linhas = [[r.tabela, r.linha, r.item, r.publicado, r.calculado, "sim" if r.confere else "NÃO"]
              for r in pub.itertuples()]
    return [("", ["Origem", "Linha", "Item", "Publicado", "Calculado", "Confere"], linhas, "")]


DINAMICAS = {"decisoes_capital": t_decisoes, "correcoes_lucro": t_correcoes,      # diretiva @nome → função
             "funil": t_funil, "lacunas": t_lacunas,
             "conferencia_resumo": t_conf_resumo, "conferencia_detalhe": t_conf_detalhe}

# =============================================================================
# 3. Leitura do roteiro
# =============================================================================
NOMES = {}                                                   # rótulos das variáveis (diretiva @nomes)


def substituir(s):
    """Troca cada {chave;decimais;tipo} pelo número calculado e formatado."""
    return re.sub(r"\{([^{};]+);(\d+);(\w+)\}",
                  lambda m: formatar(valor(m.group(1)), m.group(2), m.group(3)), s)


def ler_roteiro():
    """Converte o roteiro em uma lista de blocos: (tipo, conteúdo...)."""
    blocos, par, lista, tab = [], [], [], []                 # saída e acumuladores de parágrafo, lista e tabela

    def fecha():
        """Encerra o parágrafo, a lista ou a tabela em construção."""
        nonlocal par, lista, tab
        if par:                                              # parágrafo ou quadro de destaque ("> ")
            txt = " ".join(par)
            blocos.append(("box", txt[2:]) if txt.startswith("> ") else ("p", txt))
        if lista:                                            # lista com marcadores
            blocos.append(("ul", lista))
        if tab:                                              # tabela fixa em markdown (ignora a linha | --- |)
            linhas = [[c.strip() for c in l.strip().strip("|").split("|")] for l in tab if not re.match(r"^\|\s*-", l)]
            blocos.append(("tabela", "", linhas[0], linhas[1:], ""))
        par, lista, tab = [], [], []                         # zera os acumuladores

    for linha in C.ROTEIRO.read_text(encoding="utf-8").splitlines():      # cada linha do roteiro
        if linha.startswith("%"):                            # comentário do roteiro
            continue
        linha = substituir(linha.rstrip())                   # insere os números calculados
        if not linha.strip():                                # linha em branco separa blocos
            fecha()
        elif linha.startswith("@nomes "):                    # rótulos das variáveis
            NOMES.update(dict(x.split("=", 1) for x in linha[7:].split(";")))
        elif linha.startswith("## "):                        # seção
            fecha(); blocos.append(("h2", linha[3:]))
        elif linha.startswith("### "):                       # subseção
            fecha(); blocos.append(("h3", linha[4:]))
        elif linha.startswith("- "):                         # item de lista
            if par:
                fecha()
            lista.append(linha[2:])
        elif linha.startswith("|"):                          # linha de tabela fixa
            tab.append(linha)
        elif linha.startswith("@formula "):                  # fórmula centralizada
            fecha(); blocos.append(("formula", linha[9:]))
        elif linha.startswith("@tabela "):                   # tabela de resultados_tcc/
            fecha()
            arq, titulo, nota, cab = [x.strip() for x in linha[8:].split("|")]       # arquivo | título | nota | cabeçalhos
            df = pd.read_csv(C.TABELAS / arq, dtype=str, keep_default_na=False)    # lê como texto
            linhas = [[br(NOMES.get(v, v)) for v in r] for r in df.itertuples(index=False)]   # rótulos e vírgula
            blocos.append(("tabela", titulo, cab.split(";"), linhas, nota))
        elif linha.startswith("@"):                          # demais diretivas
            fecha()
            nome = linha[1:].strip()
            if nome in DINAMICAS:                            # tabela montada na hora
                for t in DINAMICAS[nome]():
                    blocos.append(("tabela",) + t)
            else:                                            # capa, figura1, pagina
                blocos.append((nome,))
        else:                                                # texto corrido
            if lista:
                fecha()
            par.append(linha.strip())
    fecha()                                                  # fecha o último bloco
    return blocos


# =============================================================================
# 4. Diagramação
# =============================================================================
PW, PH, ML, MR, MT, MB = 8.27, 11.69, 0.85, 0.85, 0.85, 0.95  # página A4 e margens (polegadas)
W = PW - ML - MR                                             # largura útil
CW = 0.55                                                    # largura média de um caractere no texto (fração da fonte)
CWT = 0.62                                                   # idem nas tabelas (números e negrito são mais largos)
AZUL, AZUL_CLARO, CINZA = "#1F3A5F", "#EAF2F8", "#F2F4F7"     # cores
plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})   # fonte com acentos e símbolos, embutida


def quebrar(txt, n):
    """Quebra gulosa por palavras em linhas de até n caracteres (igual à da versão em R)."""
    linhas, atual = [], ""                                   # linhas prontas e linha em construção
    for p in txt.split():                                    # cada palavra
        if not atual:                                        # primeira palavra da linha
            atual = p
        elif len(atual) + 1 + len(p) <= n:                   # cabe na linha atual
            atual += " " + p
        else:                                                # não cabe: fecha a linha
            linhas.append(atual); atual = p
    if atual:                                                # última linha
        linhas.append(atual)
    return linhas or [""]                                    # nunca devolve lista vazia


def nchar(largura, tam):
    """Quantos caracteres cabem numa largura (polegadas) com a fonte de tamanho `tam`."""
    return max(1, int(largura * 72 / (tam * CW)))            # 72 pontos por polegada


class Pagina:
    """Controla a página atual e a posição vertical (y, em polegadas a partir do topo)."""

    def __init__(self, pdf):
        self.pdf, self.n, self.fig, self.y = pdf, 0, None, MT    # arquivo, nº de páginas, figura atual, cursor

    def nova(self):
        """Fecha a página atual (com rodapé) e abre outra."""
        if self.fig is not None:
            self.rodape(); self.pdf.savefig(self.fig); plt.close(self.fig)
        self.fig = plt.figure(figsize=(PW, PH)); self.n += 1; self.y = MT

    def rodape(self):
        """Rodapé em todas as páginas, exceto a capa."""
        if self.n > 1:
            self.texto(ML, PH - 0.55, "Relatório de reprodução do TCC — versão " + LINGUAGEM, 7.5, cor="#777777")
            self.texto(PW - MR, PH - 0.55, f"página {self.n}", 7.5, cor="#777777", ha="right")

    def cabe(self, alt):
        """Abre página nova se um bloco de altura `alt` não couber."""
        if self.y + alt > PH - MB:
            self.nova()

    def texto(self, x, y, s, tam, peso="normal", estilo="normal", cor="black", ha="left"):
        """Escreve texto com o topo em (x, y) polegadas."""
        self.fig.text(x / PW, 1 - y / PH, s, fontsize=tam, fontweight=peso, fontstyle=estilo, color=cor,
                      ha=ha, va="top")                       # coordenadas da figura vão de 0 a 1, de baixo para cima

    def ret(self, x, y, w, h, cor):
        """Retângulo preenchido (faixas de tabela e quadros)."""
        self.fig.patches.append(Rectangle((x / PW, 1 - (y + h) / PH), w / PW, h / PH, transform=self.fig.transFigure,
                                          facecolor=cor, edgecolor="none", zorder=0))

    def linha_h(self, x0, x1, y, cor, esp=0.8):
        """Linha horizontal."""
        self.fig.add_artist(plt.Line2D([x0 / PW, x1 / PW], [1 - y / PH] * 2, color=cor, lw=esp,
                                       transform=self.fig.transFigure))

    def paragrafo(self, txt, tam=9.5, recuo=0.0, marcador=None, depois=0.09):
        """Parágrafo com quebra de linha e, opcionalmente, marcador de lista."""
        lh = tam * 1.42 / 72                                 # altura da linha (entrelinha 1,42)
        for i, l in enumerate(quebrar(txt, nchar(W - recuo, tam))):      # cada linha quebrada
            self.cabe(lh)                                    # quebra de página se preciso
            if i == 0 and marcador:                          # marcador "•" na primeira linha
                self.texto(ML + recuo - 0.15, self.y, marcador, tam)
            self.texto(ML + recuo, self.y, l, tam)           # a linha
            self.y += lh                                     # desce o cursor
        self.y += depois                                     # espaço após o parágrafo

    def h2(self, txt):
        """Título de seção: sempre em página nova, com fio azul."""
        self.nova()
        self.texto(ML, self.y, txt, 15, peso="bold", cor=AZUL)
        self.y += 0.32
        self.linha_h(ML, PW - MR, self.y, AZUL, 1.2)
        self.y += 0.18

    def h3(self, txt):
        """Título de subseção."""
        self.cabe(0.6)                                       # evita título órfão no pé da página
        self.y += 0.1
        self.texto(ML, self.y, txt, 11.5, peso="bold", cor=AZUL)
        self.y += 0.27

    def caixa(self, txt):
        """Quadro de destaque (linhas "> " do roteiro)."""
        tam, lh = 9.5, 9.5 * 1.42 / 72                       # fonte e entrelinha
        ls = quebrar(txt, nchar(W - 0.35, tam))              # linhas dentro do quadro
        alt = len(ls) * lh + 0.2                             # altura total
        self.cabe(alt)
        self.ret(ML, self.y, W, alt, AZUL_CLARO); self.ret(ML, self.y, 0.05, alt, "#1F6FB2")   # fundo e barra
        y = self.y + 0.1                                     # margem interna
        for l in ls:
            self.texto(ML + 0.2, y, l, tam); y += lh
        self.y += alt + 0.12

    def formula(self, txt):
        """Fórmula centralizada em itálico."""
        self.cabe(0.4)
        self.y += 0.06
        self.texto(PW / 2, self.y, txt, 10.5, estilo="italic", ha="center")
        self.y += 0.34

    def tabela(self, titulo, cab, linhas, nota, tam=8.0):
        """Tabela com cabeçalho azul, linhas zebradas, quebra de página e cabeçalho repetido."""
        if len(linhas) > 60:                                 # tabelas longas (anexo) em fonte menor
            tam = 7.0
        pad, lh = 0.05, tam * 1.3 / 72                       # margem interna e altura de linha
        ncol = len(cab)                                      # número de colunas
        comp = [min(max([len(cab[j])] + [len(r[j]) for r in linhas]), 60) for j in range(ncol)]   # caracteres por coluna
        total = max(1, int(W * 72 / (tam * CWT))) - 2 * ncol # caracteres que cabem na largura
        if sum(comp) > total:                                # reduz as colunas mais largas até caber
            limite = max(comp)
            while sum(min(c, limite) for c in comp) > total:
                limite -= 1
            comp = [min(c, limite) for c in comp]
        larg = [(c + 2) * tam * CWT / 72 for c in comp]      # largura de cada coluna (polegadas)
        larg = [w * W / sum(larg) for w in larg]             # estica para ocupar a largura útil
        xs = np.concatenate([[ML], ML + np.cumsum(larg)])    # posição de cada coluna
        cel = lambda r: [quebrar(r[j], comp[j]) if len(r[j]) > comp[j] else [r[j]] for j in range(ncol)]   # quebra nas células
        cab_q = cel(cab)                                     # cabeçalho quebrado
        alt_cab = max(len(c) for c in cab_q) * lh + 2 * pad  # altura do cabeçalho

        def desenha_cab():
            """Faixa azul com os nomes das colunas."""
            self.ret(ML, self.y, sum(larg), alt_cab, AZUL)
            for j, c in enumerate(cab_q):
                for k, l in enumerate(c):
                    self.texto(xs[j] + pad, self.y + pad + k * lh, l, tam, peso="bold", cor="white")
            self.y += alt_cab

        if titulo:                                           # título acima da tabela
            self.cabe(0.3 + alt_cab + 2 * lh)
            self.y += 0.06
            self.texto(ML, self.y, titulo, 9.5, peso="bold")
            self.y += 0.24
        else:
            self.cabe(alt_cab + 2 * lh)
        desenha_cab()
        for i, r in enumerate(linhas):                       # cada linha
            q = cel(r)                                       # células quebradas
            alt = max(len(c) for c in q) * lh + 2 * pad      # altura da linha
            if self.y + alt > PH - MB:                       # não cabe: página nova e cabeçalho repetido
                self.nova(); desenha_cab()
            if i % 2 == 1:                                   # zebrado
                self.ret(ML, self.y, sum(larg), alt, CINZA)
            for j, c in enumerate(q):                        # cada célula
                for k, l in enumerate(c):                    # cada linha da célula
                    self.texto(xs[j] + pad, self.y + pad + k * lh, l, tam,
                               peso="bold" if r[j] == "NÃO" else "normal", cor="#B00020" if r[j] == "NÃO" else "black")
            self.y += alt
        self.linha_h(ML, ML + sum(larg), self.y, AZUL, 0.8)  # fio de fechamento
        self.y += 0.05
        if nota:                                             # nota de rodapé da tabela
            self.paragrafo("Nota: " + nota, tam=7.6, depois=0.05)
        self.y += 0.1

    def figura1(self):
        """Figura 1 do TCC desenhada na página (mesma função do PNG em tabelas.py)."""
        alt = 4.4                                            # altura reservada
        self.cabe(alt + 0.6)
        self.y += 0.06
        self.texto(ML, self.y, "Figura 1. Coeficientes após a retirada de cada empresa", 9.5, peso="bold")
        self.y += 0.25
        esq, larg_p, sep = ML + 1.25, (W - 1.25 - 0.3) / 3, 0.15          # três painéis lado a lado
        axs = [self.fig.add_axes([(esq + k * (larg_p + sep)) / PW, 1 - (self.y + alt - 0.45) / PH,
                                  (larg_p - sep) / PW, (alt - 0.75) / PH]) for k in range(3)]
        desenhar_figura1(axs, coef_df, d)                    # desenha os três painéis
        self.y += alt
        self.paragrafo("Nota: pontos = coeficiente estimado sem a empresa indicada; barras = intervalo CR1 de 95%; "
                       "linha tracejada = modelo principal; losango = retirada da CEB.", tam=7.6)
        self.y += 0.08

    def capa(self):
        """Capa com título, data, linguagem e resumo da conferência."""
        self.nova()
        self.ret(0, 0, PW, 3.6, AZUL)                        # faixa azul no topo
        self.texto(ML, 1.3, "Relatório de reprodução", 26, peso="bold", cor="white")
        self.texto(ML, 1.95, "Fundamentos contábeis e capitalização de mercado", 14, cor="white")
        self.texto(ML, 2.25, "de empresas elétricas brasileiras", 14, cor="white")
        self.texto(ML, 2.8, "Rodrigo Pereira Fontes · Orientador: Prof. Marco Antonio Alves de Souza Junior", 10, cor="#D6E4F0")   # autoria
        self.texto(ML, 3.05, "MBA em Finanças e Controladoria · USP/Esalq · 2026", 10, cor="#D6E4F0")        # curso
        self.y = 4.3                                         # abaixo da faixa
        hoje = date.today().strftime("%d/%m/%Y")             # data de geração
        self.caixa(f"Gerado em {hoje} pela versão em {LINGUAGEM} do pacote de reprodução, a partir dos extratos "
                   f"preservados da CVM e da B3, sem acesso à internet.")
        sit = "todos coincidem" if n_ok == n_tot else f"{n_tot - n_ok} divergem"
        self.paragrafo(f"Conferência com o texto do TCC: {n_ok} de {n_tot} valores coincidem ({sit}).", tam=11, depois=0.12)
        self.paragrafo(f"Painel principal: {fun['minimo_quatro_anos']} observações de {d.ticker.nunique()} empresas, "
                       f"2020–2025. Painel histórico: {len(h)} observações de {h.ticker.nunique()} empresas, 2012–2025.", tam=11,
                       depois=0.12)
        r = lambda v, c: formatar(valor(f"{c}|principal|{v}"), 4, "p" if c.startswith("p") else "num")   # atalho
        self.paragrafo("Modelo principal (coeficiente; p WCR): ROE " + r("roe_lag", "coef") + "; " + r("roe_lag", "p_WCR") +
                       " · Alavancagem " + r("dl_lag", "coef") + "; " + r("dl_lag", "p_WCR") +
                       " · Porte " + r("size_lag", "coef") + "; " + r("size_lag", "p_WCR"), tam=11)

    def fecha(self):
        """Fecha a última página."""
        self.rodape(); self.pdf.savefig(self.fig); plt.close(self.fig)


# =============================================================================
# 5. Montagem
# =============================================================================
def gerar():
    """Lê o roteiro, diagrama todas as páginas e grava o PDF."""
    _carregar()                                              # resultados e conferência
    NOMES.clear()                                            # rótulos são relidos do roteiro
    blocos = ler_roteiro()                                   # blocos na ordem do roteiro
    destino = C.RESULTADOS / "relatorio_reproducao.pdf"      # arquivo de saída
    with PdfPages(destino) as pdf:                           # abre o PDF
        pg = Pagina(pdf)                                     # controlador de páginas
        for b in blocos:                                     # cada bloco vira texto, tabela ou figura
            tipo = b[0]
            if tipo == "capa":
                pg.capa()
            elif tipo == "h2":
                pg.h2(b[1])
            elif tipo == "h3":
                pg.h3(b[1])
            elif tipo == "p":
                pg.paragrafo(b[1])
            elif tipo == "box":
                pg.caixa(b[1])
            elif tipo == "ul":                               # lista: um parágrafo recuado por item
                for item in b[1]:
                    pg.paragrafo(item, recuo=0.2, marcador="•", depois=0.04)
                pg.y += 0.06
            elif tipo == "formula":
                pg.formula(b[1])
            elif tipo == "tabela":
                pg.tabela(*b[1:])
            elif tipo == "figura1":
                pg.figura1()
            elif tipo == "pagina":                           # a seção seguinte já abre página nova
                pass
            else:
                raise ValueError("diretiva desconhecida: " + tipo)
        pg.fecha()                                           # última página
        info = pdf.infodict()                                # metadados do PDF
        info["Title"] = "Relatório de reprodução do TCC"
        info["Author"] = "Rodrigo Pereira Fontes"
    print(f"  {destino.name}: {pg.n} páginas; conferência com o TCC: {n_ok} de {n_tot} valores coincidem")
    return destino
