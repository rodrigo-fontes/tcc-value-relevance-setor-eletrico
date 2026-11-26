"""
tcc.estimacao — Estimação e inferência (eq. 7, Tabelas 5 e 6 e Apêndice B do TCC)
==================================================================================

    (7)  y_it = α_i + λ_t + β1·ROE_i,t−1 + β2·AL_i,t−1 + β3·PORTE_i,t−1 + ε_it

    α_i : efeito fixo da empresa (características permanentes na janela)
    λ_t : efeito fixo do ano (movimentos comuns a todas as empresas)
    Estimação: mínimos quadrados ordinários com variáveis indicadoras (LSDV),
    uma categoria de referência em cada fator (Wooldridge, 2019; Hsiao, 2022).

Inferência (toda escrita explicitamente com álgebra de matrizes):
    CR1  Erro-padrão robusto por empresa ("cluster-robust") com correção de pequena amostra
         G/(G−1) × (N−1)/(N−K) e distribuição t(G−1) (Cameron e Miller, 2015;
         MacKinnon, Nielsen e Webb, 2023).
    WCR  Bootstrap selvagem agrupado restrito ("wild cluster restricted bootstrap"), sinais de
         Rademacher por empresa, enumeração completa das 2^G combinações
         (Cameron, Gelbach e Miller, 2008; Roodman et al., 2019). Teste prioritário do TCC.
    Holm Ajuste para a família das três hipóteses do modelo principal (Holm, 1979).
    DK   Driscoll–Kraay, núcleo de Bartlett com 1 ou 2 defasagens, fator N/(N−K), t(N−K)
         (Driscoll e Kraay, 1998; Hoechle, 2007). Comparação suplementar (Apêndice C, Tab. 4).
Diagnósticos: R² global, intra-grupo e parcial de duas vias; VIF após retirar os efeitos
fixos; fração da variação identificadora pelo teorema de Frisch–Waugh–Lovell
(Frisch e Waugh, 1933; Lovell, 1963).
"""
import numpy as np                                          # álgebra linear
import pandas as pd                                         # tabelas
from scipy.stats import t as student_t                      # distribuição t de Student
from . import config as C                                   # parâmetros de inferência


# -----------------------------------------------------------------------------
# 1. Efeitos fixos e projeções
# -----------------------------------------------------------------------------
def matriz_efeitos_fixos(dados: pd.DataFrame) -> np.ndarray:  # α_i e λ_t como indicadoras
    """Constante + indicadoras de empresa + indicadoras de ano (α_i e λ_t da eq. 7).
    Uma categoria de cada fator é omitida (referência) para não repetir a informação da constante;
    os coeficientes dos fundamentos não dependem de qual categoria é omitida."""
    ind = pd.get_dummies(dados[["ticker", "ano"]].astype({"ano": str}),   # uma coluna 0/1 por empresa e por ano
                         drop_first=True, dtype=float)      # omite a primeira categoria de cada fator
    return np.column_stack([np.ones(len(dados)), ind.to_numpy()])         # constante na primeira coluna


def residualizar(A: np.ndarray, B: np.ndarray) -> np.ndarray:  # projeção ortogonal (FWL)
    """Resíduo da projeção de B nas colunas de A: a parte de B que A não explica.
    É a operação do teorema de Frisch–Waugh–Lovell."""
    return B - A @ np.linalg.lstsq(A, B, rcond=None)[0]    # B − A (A'A)⁻¹ A'B, por mínimos quadrados


# -----------------------------------------------------------------------------
# 2. Um modelo completo
# -----------------------------------------------------------------------------
def estimar(dados: pd.DataFrame, nome: str, variaveis=None, dependente=C.DEPENDENTE,  # um modelo completo
            grupo="ticker", wcr=True, dk=True):               # grupos de inferência e testes a calcular
    """Estima a eq. (7) (ou uma variante) e devolve (linha_do_modelo, linhas_dos_coeficientes, extras).

    variaveis  : regressores além dos efeitos fixos (padrão: ROE, AL e PORTE defasados)
    dependente : 'ln_mcap' (padrão) ou 'mcap_bi' (modelo em níveis, Tabela 8)
    grupo      : coluna dos grupos de inferência ('ticker' ou 'grupo' societário)
    """
    variaveis = list(variaveis or C.FUNDAMENTOS)            # padrão: os três fundamentos
    a = dados.dropna(subset=variaveis + [dependente, grupo]).reset_index(drop=True)   # só linhas completas

    F = matriz_efeitos_fixos(a)                             # α_i e λ_t
    X = np.column_stack([F, a[variaveis].to_numpy(float)])  # matriz completa: efeitos fixos + fundamentos
    y = a[dependente].to_numpy(float)                       # variável explicada
    N, K = X.shape                                          # N observações; K parâmetros (posto total)
    assert np.linalg.matrix_rank(X) == K, "matriz sem posto completo"     # nenhuma coluna redundante

    # Mínimos quadrados: b = (X'X)⁻¹ X'y. A pseudo-inversa P = (X'X)⁻¹X' é guardada porque cada
    # coluna de P mostra o peso de cada observação em cada coeficiente (usado no CR1 e no WCR).
    P = np.linalg.pinv(X)                                   # K × N
    b = P @ y                                               # coeficientes
    e = y - X @ b                                           # resíduos ε̂
    pos = list(range(K - len(variaveis), K))                # posições dos fundamentos em b

    # Grupos de inferência
    g = pd.factorize(a[grupo])[0]                           # código 0..G−1 de cada observação
    G = g.max() + 1                                         # número de grupos (14 empresas ou 12 grupos)
    fator_cr1 = G / (G - 1) * (N - 1) / (N - K)             # correção de pequena amostra do CR1

    # CR1: V = fator × Σ_g (P_g e_g)(P_g e_g)'. Só a diagonal é necessária.
    escore = np.array([P[:, g == c] @ e[g == c] for c in range(G)])    # G × K: contribuição de cada grupo
    se_cr1 = np.sqrt(fator_cr1 * (escore ** 2).sum(axis=0))           # erro-padrão de cada coeficiente
    t_cr1 = b / se_cr1                                      # estatística t
    p_cr1 = 2 * student_t.sf(np.abs(t_cr1), G - 1)          # valor de p bilateral com t(G−1)
    crit = student_t.ppf(0.975, G - 1)                      # valor crítico do intervalo de 95%

    # R² (Apêndice B): três medidas que respondem a perguntas diferentes
    r2_global = 1 - e @ e / np.sum((y - y.mean()) ** 2)    # inclui os efeitos fixos (0,9711 no principal)
    yF = residualizar(F, y)                                 # y sem os efeitos fixos
    r2_parcial = 1 - e @ e / (yF @ yF)                      # modelo completo × só efeitos fixos (0,2896)
    med = a.groupby("ticker")                               # médias por empresa
    yw = y - med[dependente].transform("mean").to_numpy()  # y centrado por empresa
    Xw = a[variaveis].to_numpy(float) - med[variaveis].transform("mean").to_numpy()   # regressores centrados
    rw = yw - Xw @ b[pos]                                   # resíduo intra com os coeficientes de duas vias
    r2_intra = 1 - rw @ rw / (yw @ yw)                      # convenção do PanelOLS (0,2130)

    modelo = dict(modelo=nome, dependente=dependente, regressores=";".join(variaveis), agrupamento=grupo,  # resumo do modelo (Tabelas 7 e 8: N/G/K e R² intra)
                  N=N, empresas=a.ticker.nunique(), G=G, K=K, gl_residuo=N - K, anos=a.ano.nunique(),  # (continuação)
                  primeiro=int(a.ano.min()), ultimo=int(a.ano.max()),  # (continuação)
                  R2_global=r2_global, R2_intra=r2_intra, R2_parcial=r2_parcial)  # (fim)

    coefs = []                                              # uma linha por fundamento
    for v, j in zip(variaveis, pos):                          # cada fundamento
        linha = dict(modelo=nome, variavel=v, coef=b[j], se_CR1=se_cr1[j], t_CR1=t_cr1[j], p_CR1=p_cr1[j],  # coeficiente e inferência CR1
                     IC_inf=b[j] - crit * se_cr1[j], IC_sup=b[j] + crit * se_cr1[j])   # intervalo CR1 de 95%
        if wcr:                                             # bootstrap por enumeração
            exc, comb = wild_cluster_restrito(X, y, P, g, G, j, fator_cr1, abs(t_cr1[j]))  # contagem exata do WCR
            linha.update(p_WCR=exc / comb, excedencias=exc, combinacoes=comb)  # p WCR = excedências / combinações
        coefs.append(linha)                                   # guarda a linha

    if dk:                                                  # Driscoll–Kraay com 1 e 2 defasagens
        for bw in C.DEFASAGENS_DK:                            # 1 e 2 defasagens
            se_dk = driscoll_kraay(X, e, F, a.ano.to_numpy(), pos, bw)  # erros-padrão DK
            for linha, j, s in zip(coefs, pos, se_dk):        # um por fundamento
                linha[f"se_DK{bw}"] = s                       # guarda o erro-padrão
                linha[f"p_DK{bw}"] = 2 * student_t.sf(abs(b[j] / s), N - K)   # t(N−K)

    extras = dict(X=X, y=y, e=e, P=P, F=F, pos=pos, dados=a)  # usado nos diagnósticos
    return modelo, coefs, extras                              # resumo, coeficientes e matrizes


# -----------------------------------------------------------------------------
# 3. Wild cluster restricted bootstrap (WCR)
# -----------------------------------------------------------------------------
def wild_cluster_restrito(X, y, P, g, G, j, fator_cr1, t_obs, bloco=C.BLOCO_WCR):  # WCR por enumeração
    """Valor de p WCR para H0: β_j = 0 (Cameron, Gelbach e Miller, 2008; Roodman et al., 2019).

    1. Impõe a hipótese nula: estima o modelo SEM a coluna j → ajustados f0 e resíduos restritos u.
    2. Para cada vetor de sinais s (um sinal +1/−1 por grupo, mesmo sinal dentro do grupo),
       cria y* = f0 + s_g × u. As 2^G combinações são TODAS enumeradas: nada é sorteado.
    3. Reestima o modelo completo em y* e calcula t* com o mesmo erro CR1.
    4. p = proporção de combinações com |t*| ≥ |t observado|.
    Não há ajuste adicional dos resíduos pela alavancagem estatística (como declarado no TCC)."""
    R = np.delete(X, j, axis=1)                             # modelo restrito: sem o fundamento j
    f0 = R @ np.linalg.lstsq(R, y, rcond=None)[0]          # valores ajustados sob H0
    u = y - f0                                              # resíduos restritos
    total = 2 ** G                                          # 16.384 com G = 14; 4.096 com G = 12
    excedencias = 0                                         # combinações com |t*| ≥ |t|
    bits = np.arange(G, dtype=np.uint64)                    # posição de cada grupo no número binário
    for inicio in range(0, total, bloco):                   # processa em blocos para economizar memória
        ids = np.arange(inicio, min(inicio + bloco, total), dtype=np.uint64)   # números das combinações
        sinais = 2.0 * ((ids[:, None] >> bits) & 1).astype(float) - 1.0       # bit 0/1 → sinal −1/+1 (comb × G)
        Y = f0[:, None] + u[:, None] * sinais[:, g].T       # N × combinações: y* de cada combinação
        B = P @ Y                                           # coeficientes de todas as combinações de uma vez
        E = Y - X @ B                                       # resíduos de cada combinação
        esc = np.array([P[j, g == c] @ E[g == c] for c in range(G)])      # escores do coeficiente j por grupo
        t_star = B[j] / np.sqrt(fator_cr1 * (esc ** 2).sum(axis=0))      # t* com erro CR1
        excedencias += int(np.count_nonzero(np.abs(t_star) >= t_obs - C.TOL_EMPATE_WCR))  # conta |t*| ≥ |t observado|
    return excedencias, total                                 # ex.: 42 de 16.384 (ROE)


# -----------------------------------------------------------------------------
# 4. Driscoll–Kraay
# -----------------------------------------------------------------------------
def driscoll_kraay(X, e, F, anos, pos, bw):                   # erros-padrão DK
    """Erros-padrão Driscoll–Kraay dos fundamentos (Driscoll e Kraay, 1998; Hoechle, 2007).

    Admite dependência entre empresas no mesmo ano: soma-se, em cada ano, x̃·ε̂ de todas as
    empresas (x̃ = fundamentos sem os efeitos fixos) e aplica-se um estimador de variância de
    longo prazo com pesos de Bartlett w = 1 − lag/(bw+1) (Newey e West, 1987).
    Fator N/(N−K): mesma convenção de linearmodels (kernel, debiased=True)."""
    N, K = X.shape                                          # tamanho e número de parâmetros
    Xt = residualizar(F, X[:, pos])                         # fundamentos sem os efeitos fixos
    anos_unicos = np.sort(np.unique(anos))                  # T anos
    h = np.array([(Xt[anos == t] * e[anos == t, None]).sum(axis=0) for t in anos_unicos])   # T × k
    S = h.T @ h                                             # variância no mesmo ano
    for lag in range(1, bw + 1):                            # autocovariâncias até bw
        w = 1 - lag / (bw + 1)                              # peso de Bartlett
        Gm = h[lag:].T @ h[:-lag]                           # covariância entre anos distantes "lag"
        S += w * (Gm + Gm.T)                                # soma simétrica
    A = np.linalg.inv(Xt.T @ Xt)                            # "pão" do sanduíche
    V = A @ S @ A * N / (N - K)                             # variância com correção
    return np.sqrt(np.diag(V))                              # erros-padrão


# -----------------------------------------------------------------------------
# 5. Holm, VIF e concentração
# -----------------------------------------------------------------------------
def holm(p: pd.Series) -> pd.Series:                          # ajuste de Holm
    """Holm (1979): ordena os p, multiplica por m, m−1, ..., 1 e impõe monotonicidade.
    Aplicado só às três hipóteses do modelo principal; sensibilidades são exploratórias."""
    ordem = p.sort_values()                                 # do menor para o maior p
    m = len(ordem)                                          # número de hipóteses (3)
    ajust = np.maximum.accumulate(ordem.to_numpy() * np.arange(m, 0, -1)).clip(0, 1)   # 3p, 2p, 1p, monotônico
    return pd.Series(ajust, index=ordem.index).reindex(p.index)          # volta à ordem original


def vif_intra(F, Z):                                          # VIF após efeitos fixos
    """VIF após retirar os efeitos fixos: diagonal da inversa da matriz de correlação dos
    regressores residualizados. VIF próximo de 1 = pouca redundância linear."""
    Zr = residualizar(F, Z)                                 # regressores sem efeitos fixos
    corr = np.corrcoef(Zr.T)                                # correlações intra
    return np.diag(np.linalg.inv(corr)), corr               # VIF_j = [R⁻¹]_jj


def fracao_fwl(X, j):                                         # concentração da informação
    """Fração da variação que identifica β_j vinda de cada observação.

    Pelo teorema de Frisch–Waugh–Lovell, β_j depende só de z = x_j sem as demais colunas
    (efeitos fixos e outros fundamentos). A fração z_i² / Σz² mostra de onde vem a
    informação (CEB = 54,55% no ROE). Não é contribuição causal."""
    z = residualizar(np.delete(X, j, axis=1), X[:, j])      # x_j limpo das demais colunas
    return z * z / (z @ z)                                  # soma 1 entre as observações
